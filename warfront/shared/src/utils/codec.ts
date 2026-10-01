/**
 * Compact grid transport: run-length encoding with zig-zag varints, wrapped
 * in base64 so the result is plain JSON. Map grids contain long runs of the
 * same value, so this shrinks them by roughly 10x.
 */

// Available globally in browsers and Node >= 16; declared locally so the
// shared package does not depend on the DOM lib.
declare function btoa(data: string): string;
declare function atob(data: string): string;

function writeVarint(out: number[], value: number): void {
  let v = value >>> 0;
  while (v >= 0x80) {
    out.push((v & 0x7f) | 0x80);
    v >>>= 7;
  }
  out.push(v);
}

export function encodeRLE(values: ArrayLike<number>): string {
  const out: number[] = [];
  let i = 0;
  while (i < values.length) {
    const v = values[i];
    let run = 1;
    while (i + run < values.length && values[i + run] === v) run++;
    writeVarint(out, v >= 0 ? v * 2 : -v * 2 - 1);
    writeVarint(out, run);
    i += run;
  }
  return bytesToBase64(Uint8Array.from(out));
}

export function decodeRLE<T extends Uint8Array | Int16Array | Uint16Array | Int32Array>(
  encoded: string,
  target: T,
): T {
  const bytes = base64ToBytes(encoded);
  let p = 0;
  let o = 0;
  const read = (): number => {
    let result = 0;
    let shift = 0;
    for (;;) {
      const b = bytes[p++];
      result |= (b & 0x7f) << shift;
      if (b < 0x80) break;
      shift += 7;
    }
    return result >>> 0;
  };
  while (p < bytes.length && o < target.length) {
    const z = read();
    const value = z & 1 ? -((z + 1) / 2) : z / 2;
    const run = read();
    target.fill(value, o, Math.min(target.length, o + run));
    o += run;
  }
  return target;
}

export function bytesToBase64(bytes: Uint8Array): string {
  let binary = '';
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

export function base64ToBytes(b64: string): Uint8Array {
  const binary = atob(b64);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) out[i] = binary.charCodeAt(i);
  return out;
}
