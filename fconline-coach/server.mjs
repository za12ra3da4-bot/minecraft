// FC온라인 스쿼드 코치 — local server.
// Serves the page in ./public and turns squad requests into Claude calls.
//   npm start            -> needs ANTHROPIC_API_KEY (or an `ant auth login` profile)
//   npm run demo         -> no API key; answers every request with the example squad
import http from "node:http";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Anthropic from "@anthropic-ai/sdk";

const require = createRequire(import.meta.url);
const Spec = require("./public/coach-spec.js");

const here = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT) || 3000;
const HOST = process.env.HOST || "127.0.0.1";
const MODEL = process.env.CLAUDE_MODEL || "claude-opus-5";
const DEMO = process.argv.includes("--demo");
const MAX_BODY = 256 * 1024;

// The page file is written without <html>/<head>/<body>; wrap it the same way the
// claude.ai artifact viewer does.
const PAGE_OPEN =
  '<!doctype html><html lang="ko"><head><meta charset="utf-8">' +
  '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>';
const PAGE_CLOSE = "</body></html>";

const STATIC = {
  "/": { file: "public/index.html", type: "text/html; charset=utf-8", wrap: true },
  "/index.html": { file: "public/index.html", type: "text/html; charset=utf-8", wrap: true },
  "/coach-spec.js": { file: "public/coach-spec.js", type: "text/javascript; charset=utf-8" },
};

let client;
function getClient() {
  client ??= new Anthropic();
  return client;
}

function sendJson(res, status, body) {
  res.writeHead(status, { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" });
  res.end(JSON.stringify(body));
}

async function readBody(req) {
  let size = 0;
  const chunks = [];
  for await (const chunk of req) {
    size += chunk.length;
    if (size > MAX_BODY) throw new Error("body too large");
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

function describeError(err) {
  if (err instanceof Anthropic.AuthenticationError) {
    return "API 키가 없거나 올바르지 않아요. ANTHROPIC_API_KEY를 확인해 주세요.";
  }
  if (err instanceof Anthropic.PermissionDeniedError) return "이 API 키로는 모델을 쓸 권한이 없어요.";
  if (err instanceof Anthropic.NotFoundError) return `모델(${MODEL})을 찾지 못했어요. CLAUDE_MODEL 값을 확인해 주세요.`;
  if (err instanceof Anthropic.RateLimitError) return "요청이 너무 많아요. 잠시 후 다시 시도해 주세요.";
  if (err instanceof Anthropic.BadRequestError) return `요청이 거절됐어요: ${err.message}`;
  if (err instanceof Anthropic.APIConnectionError) return "Claude API에 연결하지 못했어요. 네트워크를 확인해 주세요.";
  if (err instanceof Anthropic.APIError) return `Claude API 오류 (${err.status ?? "?"}): ${err.message}`;
  if (err instanceof SyntaxError) return "코치 답변을 읽지 못했어요. 한 번 더 시도해 주세요.";
  return err?.message || "알 수 없는 오류가 났어요.";
}

async function streamDemo(send) {
  const text = JSON.stringify(Spec.EXAMPLE);
  for (let i = 1; i <= 8; i++) {
    await new Promise((r) => setTimeout(r, 250));
    send({ type: "progress", ...Spec.progressFromText(text.slice(0, Math.round((text.length * i) / 8))) });
  }
  send({ type: "result", result: Spec.EXAMPLE, model: "demo" });
}

async function handleGenerate(req, res) {
  let payload;
  try {
    payload = Spec.cleanPayload(JSON.parse(await readBody(req)));
  } catch {
    return sendJson(res, 400, { error: "요청 형식이 잘못됐어요." });
  }
  if (!payload.request) return sendJson(res, 400, { error: "원하는 스쿼드를 먼저 적어 주세요." });

  // Newline-delimited JSON: progress events while Claude writes, then one result or error.
  res.writeHead(200, { "content-type": "application/x-ndjson; charset=utf-8", "cache-control": "no-store" });
  const send = (event) => {
    if (!res.writableEnded && !res.destroyed) res.write(JSON.stringify(event) + "\n");
  };

  if (DEMO) {
    await streamDemo(send);
    return res.end();
  }

  let stream;
  try {
    stream = getClient().beta.messages.stream({
      model: MODEL,
      max_tokens: 64000,
      thinking: { type: "adaptive" },
      betas: ["server-side-fallback-2026-07-01"],
      fallbacks: "default",
      system: Spec.SYSTEM_PROMPT,
      messages: [{ role: "user", content: Spec.buildUserMessage(payload) }],
      output_config: { format: { type: "json_schema", schema: Spec.RESULT_SCHEMA } },
    });
  } catch (err) {
    send({ type: "error", message: describeError(err) });
    return res.end();
  }

  // Stop paying for tokens nobody will read.
  res.on("close", () => {
    if (!res.writableEnded) stream.abort();
  });

  let text = "";
  let lastSent = 0;
  stream.on("text", (delta) => {
    text += delta;
    const now = Date.now();
    if (now - lastSent > 400) {
      lastSent = now;
      send({ type: "progress", ...Spec.progressFromText(text) });
    }
  });

  try {
    const message = await stream.finalMessage();
    if (message.stop_reason === "refusal") {
      throw new Error("이 요청은 처리할 수 없어요. 표현을 바꿔서 다시 요청해 주세요.");
    }
    if (message.stop_reason === "max_tokens") {
      throw new Error("답변이 너무 길어져서 잘렸어요. 요청을 조금 줄여 주세요.");
    }
    const out = message.content
      .filter((block) => block.type === "text")
      .map((block) => block.text)
      .join("");
    send({ type: "result", result: Spec.normalizeResult(JSON.parse(out)), model: message.model });
  } catch (err) {
    if (err instanceof Anthropic.APIUserAbortError) return;
    console.error("[generate]", err);
    send({ type: "error", message: describeError(err) });
  } finally {
    if (!res.writableEnded) res.end();
  }
}

const server = http.createServer(async (req, res) => {
  const { pathname } = new URL(req.url, "http://localhost");
  try {
    if (req.method === "GET" && pathname === "/api/health") {
      return sendJson(res, 200, { ok: true, demo: DEMO, model: DEMO ? "demo" : MODEL });
    }
    if (req.method === "POST" && pathname === "/api/generate") {
      return await handleGenerate(req, res);
    }
    const entry = STATIC[pathname];
    if (req.method === "GET" && entry) {
      let body = await readFile(path.join(here, entry.file), "utf8");
      if (entry.wrap) body = PAGE_OPEN + body + PAGE_CLOSE;
      res.writeHead(200, { "content-type": entry.type, "cache-control": "no-cache" });
      return res.end(body);
    }
    sendJson(res, 404, { error: "not found" });
  } catch (err) {
    console.error(err);
    if (!res.headersSent) sendJson(res, 500, { error: "서버 오류가 났어요." });
    else res.end();
  }
});

server.listen(PORT, HOST, () => {
  const mode = DEMO ? "데모 모드 (API 호출 없음)" : `모델 ${MODEL}`;
  console.log(`FC온라인 스쿼드 코치: http://${HOST === "0.0.0.0" ? "localhost" : HOST}:${PORT}  [${mode}]`);
});
