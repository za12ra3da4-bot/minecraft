import 'dotenv/config';

function list(v: string | undefined): string[] {
  return (v ?? '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

/** Runtime configuration from environment variables (see .env.example). */
export const config = {
  port: Number(process.env.PORT ?? 3001),
  host: process.env.HOST ?? '0.0.0.0',
  /** Allowed browser origins for Socket.IO. Empty = allow any origin. */
  clientOrigins: list(process.env.CLIENT_ORIGIN),
  /** Directory of the built client to serve (single-service deployments). */
  clientDist: process.env.CLIENT_DIST ?? '',
};
