# Takes a Village onboarding

Welcome to Takes a Village. This guide is written for people who are brand new
to coding. You do not need to understand every file on day one. The goal is to
learn how the pieces fit together, then use the file maps and examples here when
you start reading or changing code.

## How to read this guide

Each chapter explains one concept in three ways:

1. What the concept means.
2. Where it appears in this repository.
3. A small example copied from the project code.

If you are new, read the chapters in this order:

1. Big-picture architecture.
2. Git and GitHub.
3. Docker.
4. Frontend, MVP, and TypeScript testing.
5. Backend, FSMs, WebSockets, MySQL, and Python testing.
6. GitHub Actions.

## 1. Big-picture architecture

Takes a Village is a browser game with three running services plus a database.

```text
browser
  -> frontend container
      -> serves React files
      -> proxies /api to backend
      -> proxies /ws to backend websocket
  -> backend container
      -> owns game rules and state
      -> saves data to MySQL
      -> asks bot service to spawn bots
  -> bots container
      -> joins games through backend HTTP
      -> plays games through backend WebSocket
  -> db container
      -> MySQL database
```

### Where this is in the code

- `frontend/` — the browser app and the Express proxy server.
- `service/` — the FastAPI backend and game logic.
- `bots/` — the bot service and bot players.
- `docker-compose.yml` — starts all services together.
- `Dockerfile.frontend`, `Dockerfile.backend`, `Dockerfile.bots` — build images
  for each app service.
- `service/db/schema/mysql.sql` — creates MySQL tables.

### What happens when a player clicks a button

A common gameplay action flows like this:

```text
React button click
  -> GameplayPresenter method
  -> GameplayService WebSocket packet
  -> backend /ws route
  -> process_game_event()
  -> Game.handle_action()
  -> PacketDispatcher
  -> command handler
  -> domain event / reducer / FSM
  -> updated game snapshot broadcast back to players
```

Example locations:

- `frontend/src/views/Gameplay.tsx` renders buttons and passes clicks to a presenter.
- `frontend/src/presenters/GameplayPresenter.ts` turns clicks into action commands.
- `frontend/src/service/GameplayService.ts` sends those commands over WebSocket.
- `service/api/websocket/game_router.py` receives socket packets.
- `service/api/websocket/game_events.py` routes gameplay events.
- `service/game/game.py` dispatches accepted actions.
- `service/game/state/` applies authoritative state changes.

## 2. Git

Git is the version-control tool. It tracks changes to files over time so the team
can review work, undo mistakes, and understand why code changed.

### Where this is in the code

Git metadata lives in the hidden `.git/` directory. You normally do not edit it.
You use Git from the terminal:

```bash
git status
git diff
git add README.md ONBOARDING.md
git commit -m "Update project onboarding docs"
```

### Conceptual overview

- A repository is a folder tracked by Git.
- A branch is a line of work. This repo currently has feature/refactor branches
  as well as the deploy branch used by GitHub Actions.
- A commit is a saved checkpoint.
- A diff shows what changed.
- A clean working tree means there are no uncommitted edits.

### Example from this repo

The current branch information is visible with:

```bash
git status --short --branch
```

That prints a compact branch/status summary such as:

```text
## python-refactor...origin/python-refactor
```

When you change docs or code, run `git diff` before asking for review. It is the
fastest way to check your own work.

## 3. Docker

Docker packages software into containers. A container is like a small isolated
computer running one service. Docker Compose starts several containers together
and gives them names so they can talk to each other.

### Where this is in the code

- `docker-compose.yml` — defines `db`, `backend`, `bots`, and `frontend`.
- `Dockerfile.frontend` — builds the React app and runs the Express proxy server.
- `Dockerfile.backend` — installs Python dependencies and runs FastAPI.
- `Dockerfile.bots` — installs bot dependencies and runs the bot FastAPI service.

### Conceptual overview

On your laptop, `localhost:5000` means “port 5000 on my computer.” Inside Docker,
service names are also network addresses. The backend can connect to MySQL using
the host name `db`, and the frontend proxy can connect to the backend using the
host name `backend`.

The most important lesson: the browser talks to the frontend container, and the
frontend container proxies API/WebSocket traffic to the backend container.

### Example from the code

`docker-compose.yml` tells the backend to use MySQL and find it at host `db`:

```yaml
backend:
  environment:
    DB_TYPE: mysql
    DB_HOST: db
    DB_USER: village
    DB_PASSWORD: village_db
    DB_NAME: village_db
    BOT_SERVICE_URL: http://bots:8001
```

The bot service finds the backend by Docker service name too:

```yaml
bots:
  environment:
    - GAME_SERVER_HTTP_URL=http://backend:5000
    - GAME_SERVER_WS_URL=ws://backend:5000/ws
```

The frontend Dockerfile builds the app first, then runs `server.js`:

```dockerfile
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM node:22-alpine
WORKDIR /app/frontend
COPY --from=frontend-builder /app/frontend/dist ./dist
COPY frontend/server.js ./
CMD ["node", "server.js"]
```

## 4. Frontend stack: React, TypeScript, Vite, and MVP

The frontend is what players see in the browser.

### Where this is in the code

- `frontend/package.json` — frontend dependencies and scripts.
- `frontend/src/main.tsx` — React entry point.
- `frontend/src/views/` — page-level views.
- `frontend/src/components/` — reusable UI pieces.
- `frontend/src/presenters/` — presenter classes for MVP.
- `frontend/src/service/` — API and WebSocket services.
- `frontend/src/dtos/` — TypeScript shapes for data moving across boundaries.

### Conceptual overview

- React lets us build the UI from components.
- TypeScript adds types so mistakes are caught before the browser runs the code.
- Vite starts a fast development server and builds production files.
- MVP separates the UI into Model, View, and Presenter responsibilities.

## 5. MVP: Model-View-Presenter

MVP is a design pattern. A design pattern is a reusable way to organize code.

In this project:

- Model/service: talks to the backend and owns data transfer.
- View: renders the UI and exposes simple setter/callback methods.
- Presenter: coordinates between the View and Model/service.

This keeps React components from becoming giant files that do rendering,
networking, data formatting, and game decision logic all at once.

### Where this is in the code

- Model/service example: `frontend/src/service/GameplayService.ts`.
- Presenter example: `frontend/src/presenters/GameplayPresenter.ts`.
- View example: `frontend/src/views/Gameplay.tsx`.
- Shared view base: `frontend/src/presenters/View.ts`.
- Shared presenter base: `frontend/src/presenters/Presenter.ts`.

### Example from the code: the View interface

`GameplayPresenter.ts` defines what the view must be able to do:

```ts
export interface GameplayView extends View {
  setGameState(gameState: GameStateDTO | null): void;
  setPlayerCount(playerCount: number): void;
  setTimeLeft(timeLeft: number): void;
  setUserId(userId: string): void;
  showAlert(message: string): void;
  showToast(notification: GameNotification): void;
  setConnectionState(state: ConnectionState): void;
  setChatHistory(messages: ChatMessageDTO[]): void;
  addChatMessage(message: ChatMessageDTO): void;
}
```

The presenter does not need to know whether the view uses React state, a modal,
a toast library, or something else. It only calls the interface.

### Example from the code: a Presenter method

`GameplayPresenter.ts` wraps an action command before sending it:

```ts
private dispatchAction<T>(actionCommand: string, payload: T) {
  if (!this.userId) return;

  const envelopedPayload: GameActionPayload<T> = {
    gameId: this.gameId,
    userId: this.userId,
    action_command: actionCommand,
    payload: payload
  };

  this.service.submitAction(envelopedPayload);
}
```

This means buttons can call readable methods like `buildDevelopment()` or
`finishPhase()`, while the presenter handles the WebSocket packet shape.

### Example from the code: a View creates the interface

`Gameplay.tsx` builds the object that satisfies `GameplayView`:

```tsx
const view: GameplayView = {
  setGameState,
  setPlayerCount,
  setTimeLeft,
  setUserId,
  showAlert: (msg: string) => alert(msg),
  showToast: (notification: GameNotification) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { ...notification, id }]);
  },
  setChatHistory: setMessages,
  addChatMessage: (msg: ChatMessageDTO) =>
    setMessages((prev) => [...prev, msg]),
  setConnectionState,
};
```

That object is passed to `new GameplayPresenter(view, gameId)`.

## 6. WebSockets

HTTP is good for request/response actions like “create a game.” WebSockets are
better when both sides need to keep talking over time. A multiplayer game needs
live updates, so gameplay uses WebSockets.

### Where this is in the code

- Browser WebSocket client: `frontend/src/service/GameplayService.ts`.
- Frontend proxy for `/ws`: `frontend/server.js`.
- Backend game WebSocket route: `service/api/websocket/game_router.py`.
- Backend game event router: `service/api/websocket/game_events.py`.
- Connection manager: `service/api/websocket/connection_manager.py`.
- Bot WebSocket client: `bots/botsocket.py`.

### Conceptual overview

A WebSocket starts as a normal web request, then upgrades into a persistent
connection. After that, either side can send JSON messages.

The browser sends packets shaped like:

```json
{ "event": "submit_action", "data": { "action_command": "FINISH_PHASE" } }
```

The backend responds with packets shaped like:

```json
{ "event": "game_state", "data": { "phase": "WORK" } }
```

### Example from the code: browser connection

`GameplayService.ts` chooses `ws` or `wss` based on the page protocol:

```ts
const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const host = window.location.host;
this.socket = new WebSocket(`${protocol}//${host}/ws`);
```

Using `window.location.host` is important in Docker because the browser connects
to the frontend server, and the frontend server proxies `/ws` to the backend.

### Example from the code: frontend WebSocket proxy

`frontend/server.js` forwards WebSocket traffic to the backend container:

```js
app.use(
  "/ws",
  createProxyMiddleware({
    target: "http://backend:5000",
    ws: true,
    changeOrigin: true,
    pathRewrite: (path, req) => req.originalUrl,
    logger: console,
  }),
);
```

### Example from the code: backend socket route

`service/api/websocket/game_router.py` accepts the socket and then reads packets:

```py
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_id = game_id = None
    while True:
        packet = await websocket.receive_json()
        event, payload = packet.get("event"), packet.get("data", {})
```

When it receives `join_room`, it authenticates the user, connects them to the
connection manager, sends chat history, and sends their first `game_state`.

## 7. Backend stack: FastAPI and Python services

The backend is the authority. The frontend can ask to do things, but the backend
decides whether actions are legal and how game state changes.

### Where this is in the code

- `service/main.py` — creates the FastAPI app.
- `service/container.py` — wires dependencies together.
- `service/api/router.py` — includes HTTP route modules.
- `service/game_manager/` — active games, lifecycle, game loop, persistence.
- `service/game/` — game models, serializers, state, and packet handling.
- `service/research/` — training and visualization features.
- `service/db/` — database provider contracts and implementations.

### Conceptual overview

FastAPI lets Python functions become web routes. The app starts in `main.py`.
Instead of each route creating its own dependencies, `AppContainer` creates
shared services once and passes them into route factories.

### Example from the code

`service/main.py` includes HTTP and WebSocket routers:

```py
application.include_router(create_api_router(container.api_services()))
application.include_router(create_game_ws_router(
    container.registry, container.connections, container.database,
    container.bot_client))
application.include_router(create_training_ws_router(
    container.training, container.training.runtime.update_hub))
```

`service/container.py` builds the objects those routers need:

```py
self.registry = GameRegistry()
self.lifecycle = GameLifecycleService(self.registry, ...)
self.bot_client = BotServiceClient(
    os.environ.get("BOT_SERVICE_URL", "http://bots:8001"),
    os.environ.get("BOT_SECRET", ""),
    httpx.AsyncClient,
)
self.training = TrainingService(...)
self.connections = ConnectionManager(self.registry)
```

This is dependency injection: routes receive the tools they need instead of
creating hidden globals everywhere.

## 8. FSMs: finite state machines

An FSM is a model with a limited set of states and rules for moving between
those states. Games use FSMs often because games have clear states: waiting,
running, ended; work, trade, night; stable or contested developments.

### Where this is in the code

- `service/game/state/phases.py` — day phase FSM.
- `service/game/state/player_phase.py` — player phase state values.
- `service/game/state/developments.py` — development state values.
- `service/game/state/contracts.py` — contract status transition validation.
- `service/game/state/events.py` — facts that reducers apply.
- `service/game/state/reducer.py` — reducer entry point.
- `service/game/state/event_registry.py` — event-to-reducer dispatch table.
- `service/tests/game/test_state_machines.py` — tests for FSM behavior.

### Conceptual overview

Before the refactor, game code could easily become “state update spaghetti”: one
command directly changed several objects, and another command changed some of
the same fields differently. FSMs and reducers make state changes more explicit.

The current direction is:

```text
command packet
  -> validation
  -> intent or domain event
  -> reducer/FSM applies the change
```

### Example from the code: phase FSM

`service/game/state/phases.py` has the explicit day cycle:

```py
class PhaseMachine:
    def advance(self, game):
        game._on_phase_completed(game, game.phase)

        if game.phase == Phase.WORK.value:
            self.resolver.resolve_work(game)
            game.start_phase(Phase.TRADE, resolver=self.resolver)
            return Phase.TRADE.value

        if game.phase == Phase.TRADE.value:
            self.resolver.resolve_trade(game)
            game.start_phase(Phase.NIGHT, resolver=self.resolver)
            return Phase.NIGHT.value

        if game.phase == Phase.NIGHT.value:
            self.resolver.resolve_night(game)
            game.day += 1
            game.start_phase(Phase.WORK, resolver=self.resolver)
            return Phase.WORK.value
```

### Example from the code: player phase states

`service/game/state/player_phase.py` names the player states:

```py
class PlayerPhaseState(str, Enum):
    ACTIVE = "ACTIVE"
    INTENT_SUBMITTED = "INTENT_SUBMITTED"
    NEEDS_REPLACEMENT = "NEEDS_REPLACEMENT"
    RESOLVED = "RESOLVED"
    DEAD = "DEAD"
```

This is clearer than asking only “is `finished_phase` true?” because it explains
why a player is or is not available to act.

### Example from the code: reducer dispatch

`service/game/state/reducer.py` applies domain events:

```py
class GameStateReducer(...):
    def apply(self, game, event):
        game.domain_events.append(event)
        applier_name = EVENT_APPLIERS.get(type(event))
        if applier_name:
            return getattr(self, applier_name)(game, event)
        raise ValueError(f"Unsupported event: {event!r}")
```

The matching registry in `service/game/state/event_registry.py` avoids a giant
if/else chain:

```py
EVENT_APPLIERS = {
    ContractCreated: "_apply_contract_created",
    PlayerResourcesGained: "_apply_resources_gained",
    DevelopmentBuilt: "_apply_development_built",
    FireStarted: "_apply_fire_started",
}
```

## 9. MySQL

MySQL is the database used by Docker and production-style runs. It stores users,
game history, phase snapshots, completed games, training batches, visualizations,
and genomes.

### Where this is in the code

- `docker-compose.yml` — starts the `mysql:8.0` container.
- `service/db/factory.py` — chooses memory or MySQL provider.
- `service/db/mysql/provider.py` — connects to MySQL and initializes tables.
- `service/db/schema/mysql.sql` — table definitions.
- `service/db/mysql/*.py` — repository code for specific data areas.
- `service/tests/db/` — database provider and MySQL tests.

### Conceptual overview

The backend can run with either:

- `DB_TYPE=memory` for fast local development/tests; or
- `DB_TYPE=mysql` for persistent storage.

The rest of the app talks through database contracts/facades so most code does
not need to know which provider is active.

### Example from the code: provider selection

`service/db/factory.py` chooses the database provider:

```py
def get_database(config: dict[str, Any] | None = None):
    resolved = config or load_config()
    if resolved.get("db_type") == "memory":
        return InMemoryDB()
    return DatabaseFacade(MySQLDB(resolved["db"]))
```

### Example from the code: MySQL connection retry

`service/db/mysql/provider.py` retries the connection because the database
container may still be starting:

```py
def get_connection(self):
    attempts = 10
    for attempt in range(attempts):
        try:
            conn = mysql.connector.connect(**self.config)
            db_logger.info("Connected to MySQL")
            return conn
        except mysql.connector.Error as err:
            db_logger.warning(
                f"MySQL connection attempt {attempt + 1}/{attempts} failed: {err}"
            )
            time.sleep(3)
```

### Example from the code: a table

`service/db/schema/mysql.sql` defines tables like `games`:

```sql
CREATE TABLE IF NOT EXISTS `games` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `game_id` VARCHAR(64) NOT NULL UNIQUE,
    `day_num` INT NOT NULL,
    `phase` VARCHAR(32) NOT NULL,
    `data` JSON NOT NULL,
    `game_type` VARCHAR(32) NOT NULL DEFAULT 'human',
    `training_batch_id` VARCHAR(64),
    `training_generation` INT,
    `trade_count` INT NOT NULL DEFAULT 0,
    `contest_count` INT NOT NULL DEFAULT 0,
    `lie_count` INT NOT NULL DEFAULT 0
);
```

## 10. Testing TypeScript

Frontend tests check presenter behavior, service behavior, and React components.

### Where this is in the code

- `frontend/package.json` — scripts: `test`, `build`, `lint`.
- `frontend/jest.config.json` — Jest configuration.
- `frontend/test/` — frontend tests.
- `frontend/test/research-presenter.test.ts` — presenter test example.
- `frontend/test/new-game-modal.test.tsx` — component test example.

### Conceptual overview

Testing means writing code that checks other code. Frontend tests are useful
because they can catch broken UI logic before a human clicks through the app.

Run tests with:

```bash
cd frontend
npm test
```

Build/type-check with:

```bash
cd frontend
npm run build
```

### Example from the code

`frontend/package.json` defines the scripts:

```json
"scripts": {
  "dev": "vite",
  "build": "tsc && vite build",
  "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
  "test": "jest --coverage"
}
```

`frontend/jest.config.json` tells Jest where tests live:

```json
{
  "testEnvironment": "jest-environment-jsdom",
  "testMatch": ["<rootDir>/test/**/*.test.{ts,tsx}"],
  "collectCoverage": true
}
```

`frontend/test/research-presenter.test.ts` creates a fake view and checks that
the presenter updates it:

```ts
function createView(): ResearchView & { calls: Record<string, unknown[]> } {
  const calls: Record<string, unknown[]> = {};
  const record = (name: string) => (value: unknown) => {
    calls[name] = [...(calls[name] ?? []), value];
  };
  return {
    calls,
    setGames: record("games"),
    setTrainingBatches: record("trainingBatches"),
    setErrorMessage: record("errorMessage"),
  } as ResearchView & { calls: Record<string, unknown[]> };
}
```

That is MVP helping testing: the test can fake the View interface without
rendering the whole app.

## 11. Testing Python

Python tests check backend routes, game rules, state machines, persistence, bot
helpers, and training/research services.

### Where this is in the code

- `requirements-dev.txt` — includes `pytest`.
- `service/tests/` — backend tests.
- `service/tests/game/test_state_machines.py` — FSM/reducer tests.
- `service/tests/websocket/` — WebSocket tests.
- `service/tests/db/` — database tests.
- `bots/tests/` — bot tests.

### Conceptual overview

Backend tests usually create a small game or test app, perform an action, and
assert that the resulting state is correct. Good tests are especially important
for game logic because one rule change can accidentally break another phase.

Run tests with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```

Run a quick syntax check with:

```bash
python3 -m compileall -q service bots
```

### Example from the code

`service/tests/game/test_state_machines.py` verifies the phase FSM:

```py
def test_phase_machine_resolves_and_enters_next_phase(make_game):
    game = make_game()
    game.start_game()
    calls = []

    class RecordingResolver:
        @staticmethod
        def resolve_work(game_state):
            calls.append(("resolve", game_state.phase))

    machine = PhaseMachine(RecordingResolver)
    machine.advance(game)

    assert calls == [("resolve", "WORK")]
    assert game.phase == "TRADE"
```

The same file checks that every domain event has a reducer applier:

```py
def test_every_domain_event_has_registered_state_applier():
    event_types = {
        event_type
        for event_type in vars(events).values()
        if isinstance(event_type, type)
        and getattr(event_type, "__module__", None) == events.__name__
    }

    assert event_types
    assert event_types <= set(EVENT_APPLIERS)
```

That test protects the reducer architecture. If someone adds a new event but
forgets to register how it changes state, the test fails.

## 12. GitHub Actions

GitHub Actions runs automation on GitHub. This repo currently uses it for home
lab deployment when code is pushed to `main`.

### Where this is in the code

- `.github/workflows/deploy.yml` — deploy workflow.

### Conceptual overview

A workflow is a YAML file. It says:

- when to run;
- what machine to run on;
- what secret environment variables are needed;
- which shell commands to execute.

This project's workflow installs `cloudflared`, opens an SSH connection through
a Cloudflare Access tunnel, pulls the latest code on the server, and rebuilds
Docker Compose services.

### Example from the code

`.github/workflows/deploy.yml` runs on pushes to `main`:

```yaml
on:
  push:
    branches:
      - main
```

It receives secrets from GitHub:

```yaml
env:
  SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
  SERVER_USER: ${{ secrets.SERVER_USER }}
  CF_HOSTNAME: ${{ secrets.CF_HOSTNAME }}
  CF_CLIENT_ID: ${{ secrets.CF_CLIENT_ID }}
  CF_CLIENT_SECRET: ${{ secrets.CF_CLIENT_SECRET }}
```

Then the remote server pulls and rebuilds containers:

```bash
cd /home/tav/takesAVillage
GIT_SSH_COMMAND="ssh -i ~/.ssh/github_actions -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" git pull origin main
docker compose up -d --build frontend backend bots db
docker image prune -f
```

Important safety note: never print secrets in logs and never commit real secret
values. Use `.env.example` for placeholders and GitHub repository secrets for
deployment credentials.

## 13. First tasks for a new contributor

If you are new to coding, start with reading tasks before changing behavior.

1. Run `git status --short --branch` and confirm your workspace state.
2. Start the app with Docker Compose: `docker compose up --build`.
3. Open <http://localhost:4999> and create a game.
4. Read `frontend/src/views/Gameplay.tsx` and find one button.
5. Follow that button into `frontend/src/presenters/GameplayPresenter.ts`.
6. Follow the presenter call into `frontend/src/service/GameplayService.ts`.
7. Find the matching backend event in `service/api/websocket/game_events.py`.
8. Follow `Game.handle_action()` into `service/game/packet_handling/dispatcher.py`.
9. Find where the command emits or applies state changes in `service/game/state/`.
10. Run the relevant tests before and after your change.

## 14. Vocabulary

- API: a boundary where one program asks another program to do something.
- Backend: server-side code; users do not see it directly.
- Container: an isolated runtime for one service.
- DTO: data-transfer object; a typed shape for data crossing a boundary.
- Event: a fact that something happened in the game.
- FSM: finite state machine; named states plus allowed transitions.
- Frontend: browser-side code; users see and interact with it.
- Model: in MVP, the data/service layer.
- Presenter: in MVP, the coordinator between user intent and data/service calls.
- Proxy: a server that forwards traffic to another server.
- Reducer: code that takes current state plus an event and applies the state change.
- View: in MVP, the rendering layer.
- WebSocket: a persistent two-way connection between browser and server.

## 15. Mental model to keep

The frontend is not the authority. It is a friendly interface for the player.

The backend is the authority. It validates commands, advances FSMs, applies
events through reducers, persists snapshots/results, and broadcasts player
specific views of the game.

Docker is the local miniature production environment. It lets the frontend,
backend, bots, and MySQL run together the same way they do when deployed.
