# Takes a Village

Takes a Village is a multiplayer social-dilemma game about specialization,
cooperation, negotiation, deception, and survival. Players gather resources,
build developments, trade with each other, hire workers, contest ownership, and
try to keep their village alive through repeated day/night cycles.

The codebase is intentionally split into small services so students can learn
how a browser game, an API, autonomous bots, WebSockets, Docker, and MySQL fit
together in a real project.

## Game loop

Each in-game day moves through an explicit finite state machine (FSM):

1. `WORK` — players build, maintain, upgrade, work developments, or contest a
   development.
2. `TRADE` — players negotiate, accept/deny/counter contracts, and finalize
   trades or wages.
3. `NIGHT` — players eat food, stay warm by starting or joining fires, and may
   become sick, recover, or die.

The backend owns the authoritative game state. The frontend sends player
commands over WebSocket; backend command handlers validate them and emit domain
events; reducers apply those events to the game state.

## Services

- `frontend/` — React, TypeScript, Vite, and an Express production server. The
  React app uses Model-View-Presenter (MVP): views render UI, presenters handle
  user intent, and service classes talk to HTTP/WebSocket endpoints.
- `service/` — FastAPI backend. It owns API routes, WebSocket routing, active
  game lifecycle, FSM/reducer game logic, persistence, research tooling, and bot
  orchestration hooks.
- `bots/` — FastAPI bot service plus autonomous bot models. Bots join games over
  HTTP, then play over the same WebSocket protocol as people.
- `db` Docker service — MySQL 8.0 for persisted users, finished games, research
  snapshots, training batches, visualizations, and genomes.

In Docker, browser traffic enters the frontend container first. The Express
server serves the compiled React app and proxies `/api` and `/ws` to the backend
container.

```text
browser
  -> frontend container on :4999
      -> static React files from frontend/dist
      -> /api proxy to backend:5000
      -> /ws proxy to backend:5000/ws
  -> backend container
      -> MySQL db container
      -> bots container for bot spawning/training
```

## Getting started with Docker

Docker Compose is the easiest way to run the whole stack.

```bash
cp .env.example .env
# Edit BOT_SECRET in .env. Generate one with:
# python3 -c 'import secrets; print(secrets.token_urlsafe(48))'

docker compose up --build
```

Default local ports:

- frontend: http://localhost:4999
- backend API: http://localhost:5000
- bot service: http://localhost:8001
- MySQL: localhost:3308

## Local development

Backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
DB_TYPE=memory python3 -m uvicorn service.main:app --reload --port 5000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server runs at http://localhost:5173. The production Docker
frontend uses `frontend/server.js` instead, because that server also proxies API
and WebSocket traffic inside the Docker network.

## Testing

Python backend and bot tests use pytest:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
python3 -m compileall -q service bots
```

Frontend tests use Jest and React Testing Library:

```bash
cd frontend
npm test
npm run build
```

## Where to learn more

- `ONBOARDING.md` — a beginner-friendly guide to the full stack, with chapters
  on MVP, Docker, git, GitHub Actions, testing, FSMs, WebSockets, and MySQL.
- `frontend/README.md` — frontend setup and MVP architecture.
- `service/README.md` — backend setup, package responsibilities, and FSM/reducer
  architecture.