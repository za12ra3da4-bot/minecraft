import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createGameServer } from './app';
import { config } from './config';

const here = dirname(fileURLToPath(import.meta.url));
const server = createGameServer({
  clientOrigins: config.clientOrigins,
  clientDistCandidates: [config.clientDist, resolve(here, '../../client/dist'), resolve(here, '../client/dist')],
});

server.httpServer.listen(config.port, config.host, () => {
  console.log(`WARFRONT server listening on http://${config.host}:${config.port}`);
});

const shutdown = (): void => {
  void server.close().then(() => process.exit(0));
  setTimeout(() => process.exit(0), 3000).unref();
};
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
