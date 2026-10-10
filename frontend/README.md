# Takes a Village frontend

The frontend is a React application built with TypeScript and Vite. It renders
the browser game client, talks to the backend API, and keeps a live WebSocket
connection open while a player is in a game.

## Tech stack

- React — component-based user interfaces.
- TypeScript — typed JavaScript for safer DTOs, presenters, and component props.
- Vite — fast local development and production builds.
- React Router — routes such as home, play, gameplay, instructions, and research.
- Native WebSocket — real-time game state, chat, lobby, and training updates.
- Jest + React Testing Library — TypeScript and component tests.
- Express + `http-proxy-middleware` — production static file server and Docker
  proxy for `/api` and `/ws` traffic.

## Model-View-Presenter layout

The UI follows Model-View-Presenter (MVP):

- Models/services live in `src/service/`. They make HTTP requests, manage
  WebSocket connections, and expose callbacks. Example:
  `src/service/GameplayService.ts` opens a browser WebSocket at
  `${protocol}//${host}/ws` and emits packets like `join_room`, `send_chat`, and
  `submit_action`.
- Presenters live in `src/presenters/`. They receive user intent from views,
  build DTO payloads, call services, and push display updates back into a view
  interface. Example: `src/presenters/GameplayPresenter.ts` wraps a gameplay
  command in `{ gameId, userId, action_command, payload }` before calling
  `GameplayService.submitAction()`.
- Views live in `src/views/` and `src/components/`. They render React UI and
  delegate decisions to presenters. Example: `src/views/Gameplay.tsx` builds a
  `GameplayView` object with setters such as `setGameState`, `setTimeLeft`, and
  `showToast`, then passes user clicks to the presenter.

This separation makes presenter and service behavior easier to test without
needing a browser for every case.

## Project structure

```text
frontend/
├── server.js              # Express server for production Docker builds
├── package.json           # npm scripts and dependencies
├── jest.config.json       # Jest test configuration
├── src/
│   ├── components/        # reusable React components
│   ├── dtos/              # shared frontend data-transfer types
│   ├── presenters/        # MVP presenter classes and view interfaces
│   ├── service/           # API/WebSocket client classes
│   └── views/             # route-level React views
└── test/                  # Jest tests
```

## Run locally

```bash
npm install
npm run dev
```

Vite serves the development app at http://localhost:5173.

## Build and test

```bash
npm test
npm run build
npm run lint
```

`npm test` runs Jest with coverage. `npm run build` type-checks with `tsc` and
then produces the Vite production bundle in `dist/`.

## Docker behavior

The Docker image builds the React app in one Node stage, then runs
`frontend/server.js` in a smaller production stage. That Express server:

- serves static files from `dist/`;
- proxies `/api` to `http://backend:5000`;
- proxies `/ws` to `http://backend:5000/ws` with WebSocket support;
- falls back to `index.html` so React Router can handle browser routes.

See the root `ONBOARDING.md` for a beginner-friendly walkthrough of how the
frontend fits into the full Docker stack.