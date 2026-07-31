# Takes a Village backend

The backend is a FastAPI application. Run commands from the repository root so
the package-qualified `service.*` imports resolve consistently.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
DB_TYPE=memory python3 -m uvicorn service.main:app --reload --port 5000
```

Set `DB_TYPE=mysql` plus `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` to
use MySQL. Memory mode is suitable for local development and tests.

## Architecture

- `game/` owns game state, models, actions, rules, phases, and serializers. It
  does not depend on HTTP, WebSockets, persistence globals, or training.
- `game_manager/` owns the active-game registry, game creation, ticking,
  completed-game persistence, and the bot-service client.
- `db/` defines persistence contracts and memory/MySQL providers behind one
  facade. Provider construction lives in `db/factory.py`; initialization occurs
  in the application lifespan.
- `research/training/` owns training orchestration and exposes `TrainingService`.
- `research/visualizations/` owns visualization commands, rendering, and caching.
- `api/routers/` and `api/websocket/` translate HTTP/WebSocket traffic only.
- `container.py` and `main.py` compose dependencies and own startup/shutdown.

Dependencies point inward: transport depends on application services, managers
depend on the game and persistence contracts, and the game package remains
transport- and persistence-independent.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
python3 -m compileall -q service bots
cd frontend && npm test -- --runInBand && npm run build
```

The MySQL provider requires a disposable MySQL service for integration testing;
the default suite exercises its schema and query construction without connecting.