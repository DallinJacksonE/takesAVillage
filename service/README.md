# Takes a Village service

The backend is a Node 22 TypeScript service built with Fastify. Run workspace
commands from the repository root so `@takes-a-village/shared` builds before the
service and frontend consumers.

## Local setup

```bash
npm ci
cp service/config.example.json service/config.json
chmod 600 service/config.json
# Replace every placeholder in service/config.json.
npm run build -w shared
npm run build -w service
SERVICE_CONFIG_PATH=service/config.json npm start -w service
```

`service/config.json` is ignored and is the only source for database credentials,
the bot shared secret, and internal service URLs. `SERVICE_CONFIG_PATH` only
locates that file. Do not put private values in `frontend/config.json`.

## Architecture

- `src/game/` owns game state, models, actions, rules, phases, and serializers.
- `src/game-manager/` owns active games, ticking, persistence, and bot requests.
- `src/db/` defines memory and MySQL providers using the retained MySQL schema.
- `src/research/training/` owns training orchestration.
- `src/research/visualizations/` generates and stores deterministic SVG output.
- `src/api/` translates HTTP and WebSocket traffic.
- `src/app.ts` and `src/main.ts` compose dependencies and startup/shutdown.

All network contracts come from `@takes-a-village/shared`; service-local boundary
interfaces must not duplicate those schemas.

## Validation

```bash
npm run test -w service
SERVICE_COMMAND='node service/dist/main.js' npm run test:characterization -w service
npm run typecheck -w service
npm run build -w service
```

Set `MYSQL_TEST_CONFIG_PATH` to a disposable JSON MySQL configuration when running
the live provider integration test; the default suite skips that external test.