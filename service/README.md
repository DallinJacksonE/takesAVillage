# Takes a Village backend

The backend is a FastAPI application. It owns the authoritative game state,
HTTP API routes, WebSocket routing, game lifecycle, persistence, research tools,
and the FSM/reducer game-logic layer.

Run backend commands from the repository root so package-qualified `service.*`
imports resolve consistently.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
DB_TYPE=memory python3 -m uvicorn service.main:app --reload --port 5000
```

Use memory mode for fast local development and tests. Use MySQL by setting:

```bash
DB_TYPE=mysql
DB_HOST=127.0.0.1
DB_USER=village
DB_PASSWORD=village_db
DB_NAME=village_db
```

Docker Compose sets those values automatically for the backend container.

## Architecture

- `main.py` creates the FastAPI app, includes HTTP and WebSocket routers, and
  starts background game/training loops during application lifespan.
- `container.py` wires shared dependencies: database provider, game registry,
  game lifecycle service, connection manager, bot-service client, training
  service, and visualization service.
- `api/routers/` contains HTTP route factories for sessions, games, research,
  training, genomes, and visualizations.
- `api/websocket/` contains the `/ws` game socket, the training socket, and the
  connection manager that broadcasts player-specific game snapshots.
- `game/packet_handling/` parses incoming gameplay command packets and routes
  accepted commands into the state layer. This package is transport-adjacent;
  it should not become the long-term home for authoritative state mutation.
- `game/state/` owns finite state machines, domain events, event dispatch, legal
  actions, projections, reducers, and phase resolution helpers.
- `game/models/` contains mostly data-oriented game objects such as players,
  maps, developments, chats, and contracts.
- `game_manager/` owns active-game registry, lifecycle operations, background
  ticking, finished-game persistence, and bot-service communication.
- `db/` defines persistence contracts and memory/MySQL providers behind a
  facade. Provider selection lives in `db/factory.py`.
- `research/` contains training orchestration, update streams, visualization
  commands, and visualization caching.

Dependencies point inward: transport depends on application services, managers
depend on game and persistence contracts, and the game state package should stay
independent of HTTP, WebSockets, and concrete database providers.

## FSM and reducer game logic

The game logic has been moved toward explicit state machines and domain events.
Important files:

- `game/state/phases.py` — `PhaseMachine` advances `WORK -> TRADE -> NIGHT -> WORK`.
- `game/state/player_phase.py` — `PlayerPhaseState` replaces raw boolean phase
  lock thinking while preserving `finished_phase` as a compatibility projection.
- `game/state/developments.py` — `DevelopmentState` defines `STABLE` and
  `CONTESTED`, and `MapDevelopmentStore` keeps map-backed developments as the
  authoritative store.
- `game/state/events.py` — dataclass domain events such as
  `PlayerResourcesGained`, `DevelopmentContestActivated`, and `TradeFinalized`.
- `game/state/event_registry.py` — maps event classes to reducer applier methods.
- `game/state/reducer.py` — `GameStateReducer.apply()` appends the event to
  `game.domain_events` and dispatches it to a domain reducer mixin.
- `game/state/*_reducer.py` — domain-specific reducer methods for contracts,
  resources, developments, phase state, and campfires.

The intended flow is:

```text
WebSocket packet
  -> game_events.process_game_event()
  -> Game.handle_action()
  -> PacketDispatcher
  -> command validation / intent creation
  -> Game.apply_event() or Game.apply_events()
  -> GameStateReducer
  -> updated game state
  -> player-specific serialized snapshot
```

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
python3 -m compileall -q service bots
```

Frontend validation lives under `frontend/`:

```bash
cd frontend
npm test
npm run build
```

The default test suite uses memory persistence where possible. MySQL-specific
tests mostly exercise schema/query behavior without requiring a live database;
full integration testing needs a disposable MySQL service.