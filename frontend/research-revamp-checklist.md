# Research Dashboard Revamp Checklist

Goal: overhaul the research experience so researchers can browse games and training batches, distinguish training data from human/human-bot games, inspect generated visualizations, and monitor live training loops without losing the existing MVP frontend boundaries.

Current context observed in this repo:
- Frontend research page is currently one large React view: `frontend/src/views/Research.tsx`.
- Existing MVP boundary is partial: `frontend/src/presenters/ResearchPresenter.ts` loads games and owns the training-session WebSocket subscription; `frontend/src/service/ResearchService.ts` hides `/api/research/games` and `/ws/research/training-sessions`.
- DTOs live in `dtos/index.ts`. Current research DTOs include `ResearchGameDTO` and `TrainingSessionDTO`.
- Backend research endpoints are in `service/api.py`: `/api/research/games`, `/api/research/genomes`, `/api/research/train`, `/api/research/training-sessions`, and `/ws/research/training-sessions`.
- Current MySQL tables are created in `service/db.py`. Stored complete games live in `games`; phase history lives in `game_history`, `work_phase_snapshots`, `trade_phase_snapshots`, and `night_phase_snapshots`.
- `service/training_orchestrator.py` already tracks active sessions in memory and stores generation fitness statistics in `generation_statistics`, but completed training sessions/batches are not persisted as first-class records.
- `service/db.py` has a `store_visualization()` method stub for MySQL and an in-memory implementation, but there is no persisted visualization table or serving endpoint yet.

Guiding decisions to keep unless we explicitly revisit them:
- Use first-class training batch metadata in SQL instead of encoding only a batch number in `game_id`. Game IDs may still include a human-readable prefix/suffix for debugging, but DB columns should be the source of truth.
- Treat a training batch as the durable historical object for a training loop. Active loops and completed loops should appear in the same left-column training list.
- Keep visualization generation on the backend; the frontend should receive metadata and image URLs, not run matplotlib/seaborn.
- Implement visualization generation with a command pattern: each visualization is a small class with a stable `name`, `title`, and `render(context)`-style method. Registries/run-all commands should assemble available visualizations without `if/elif` chains.
- Keep React components thin. Search/sort/filter behavior can be presenter-owned; HTTP/WebSocket details stay in `ResearchService`.
- Prefer generated PNG/SVG assets stored and served by the backend over embedding large base64 payloads in list responses.

Open questions / decisions to clarify:
- [ ] What should count as the “best player” for the inventory-over-time chart: highest final fitness, highest final resource total, longest survival, winner if the game has one, or first configured champion bot?
- [ ] Should batch visualizations include only completed games, or include the current in-progress game as partial data when a loop is still running?
- [ ] What exact contest event should be counted: contest actions submitted, contests initiated, contests resolved, contested development ownership changes, or all of the above as separate series?
- [ ] Should “developments built by players” mean final ownership, build events over time, upgrade/maintenance events, or all development events grouped by player?
- [ ] Should generated visualization files be regenerated on every request, generated when each game/batch completes, or lazily generated once and cached?
- [ ] How long should completed training batches and visualization images be retained?
- [ ] Do researchers need to download raw CSV/JSON behind each visualization in this revamp, or is image + expandable parsed game data enough for the first pass?

## Phase 1: Data model and API contracts

- [x] Add durable training batch identity.
  - Backend likely files: `service/db.py`, `service/training_orchestrator.py`, `service/game_manager.py`.
  - Add a `training_batches` table with at least: `batch_id`, `status`, `ruleset`, `bot_model`, `bot_count`, `total_generations`, `current_generation`, `current_game_id`, `started_at`, `completed_at`, `base_genome_id`, `final_champion_genome_id`, and JSON config for mutation/selection settings.
  - Add `training_batch_id` / `training_generation` columns to the durable game record so training games can be grouped without parsing `game_id`.
  - Keep `game_id` stable and unique; optional readable form can be `train_<batchShort>_g<generation>_<uuidShort>` if we still want visual traceability.

- [x] Update DB provider contract and both providers.
  - Backend file: `service/db.py`.
  - Extend `DatabaseProvider` with methods such as `create_training_batch`, `mark_training_batch_game_started`, `append_training_batch_generation_stats`, `complete_training_batch`, `get_training_batches`, and `get_training_batch(batch_id)`.
  - Implement both `InMemoryDB` and `MySQLDB` versions so dev mode stays usable.

- [x] Persist active and completed training-loop progress.
  - Backend files: `service/training_orchestrator.py`, `service/training_session_presenter.py`, `service/training_updates.py`.
  - When `start_training_session()` creates `session_id`, also create/persist a training batch.
  - When `_trigger_next_generation()` creates a game, attach the batch id/generation to the game record.
  - When `handle_training_game_ended()` computes `generation_statistics`, append those stats to the training batch.
  - When the loop finishes, mark the batch complete and keep it queryable after it leaves `active_training_sessions`.

- [x] Add list/detail API endpoints for games and batches.
  - Backend file: `service/api.py`.
  - Replace or extend `/api/research/games` so the list supports search/sort inputs and returns compact rows, not full parsed game payloads for every row.
  - Add `/api/research/games/{game_id}` for full game details, parsed game data, and visualization metadata.
  - Add `/api/research/training-batches` for compact batch rows, including in-progress status.
  - Add `/api/research/training-batches/{batch_id}` for batch details, linked games, generation statistics, and visualization metadata.
  - Keep `/api/research/training-sessions` and the WebSocket as live-update sources, but normalize their shape with the persisted batch DTO where practical.

- [x] Update shared DTOs.
  - File: `dtos/index.ts`.
  - Add `ResearchGameListItemDTO`, `ResearchGameDetailDTO`, `ResearchVisualizationDTO`, `TrainingBatchListItemDTO`, `TrainingBatchDetailDTO`, and a stronger `TrainingGenerationStatisticsDTO`.
  - Include fields needed for search/sort display: id/name, created/started/completed timestamps, status, game type (`human`, `human_bot`, `training`), batch id, generation number, ruleset, bot model, and summary counts.

## Phase 2: Visualization backend with command pattern

- [x] Create a visualization module.
  - Backend likely new package: `service/research_visualizations/`.
  - Suggested files:
    - `service/research_visualizations/context.py` (deferred until contexts need behavior beyond dict DTOs)
    - `service/research_visualizations/command.py`
    - `service/research_visualizations/game_commands.py`
    - `service/research_visualizations/batch_commands.py`
    - `service/research_visualizations/registry.py`
    - `service/research_visualizations/runner.py`
  - Keep matplotlib/seaborn imports isolated here so visualization dependencies do not leak through game orchestration code.

- [x] Define the visualization command interfaces.
  - `GameVisualizationCommand`: `name`, `title`, `description`, `render(context) -> Figure`.
  - `TrainingBatchVisualizationCommand`: same interface, but accepts batch-level context.
  - Add a runner that takes a context plus a registry of commands and stores all generated outputs through the DB/storage layer.

- [x] Implement durable visualization storage.
  - Backend file: `service/db.py`.
  - Add a `research_visualizations` table with at least: `id`, `scope_type` (`game` or `training_batch`), `scope_id`, `name`, `title`, `mime_type`, `image_bytes` or `storage_path`, `created_at`, and optional JSON metadata.
  - Finish `MySQLDB.store_visualization()` or replace it with explicit `store_research_visualization()` / `get_research_visualizations()` methods.
  - Add a serving endpoint such as `/api/research/visualizations/{visualization_id}` that returns the image with the correct content type.

- [x] Build game visualization commands.
  - Inventory over time for the best player.
    - Inputs: per-day player resource snapshots from `games.data.players` and/or phase snapshots.
    - Output: line chart with food/wood/iron across days.
  - Trades per bot/player.
    - Inputs: `trade_history` from player snapshots / trade phase snapshots.
    - Output: bar chart of accepted/completed trades by player, with bot/human label if available.
  - Developments built by players.
    - Inputs: player `developments`, map/development state, and action/timeline data if available.
    - Output: grouped bar chart or timeline grouped by player and development type.
  - Contests.
    - Inputs: contest committed actions, contested developments, and/or timeline events.
    - Output: chart/table-like visualization of contests by day/player/development.

- [x] Build training batch visualization commands.
  - Champion fitness and average fitness over games/generations on the same chart.
    - Inputs: persisted `generation_statistics`; current code already provides `best_fitness`, but average fitness may need to be added to `service/training_population.py` because it currently stores best/median/worst, survival, resources, developments, illegal actions, and gene diversity.
  - Trading and contesting per game.
    - Inputs: linked game ids in the batch plus game-level trade/contest counts.
    - Output: two-series line/bar chart per generation/game.

- [x] Trigger visualization generation at lifecycle boundaries.
  - Game visualizations: lazily generate when a completed game detail is first requested.
  - Batch visualizations: lazily generate when a training batch detail is first requested.
  - Ensure generation failures are logged but do not break game completion or training-loop progression.

- [x] Add backend tests for visualization commands.
  - Test command classes with small synthetic game/batch contexts.
  - Verify figures are created without requiring a display backend; set/use a non-interactive matplotlib backend if needed.
  - Verify the registry can add a new command without changing runner control flow.

## Phase 3: Research frontend MVP restructuring

- [x] Split `frontend/src/views/Research.tsx` into thin components.
  - Likely new files:
    - `frontend/src/components/research/ResearchLayout.tsx`
    - `frontend/src/components/research/ResearchSidebar.tsx`
    - `frontend/src/components/research/ResearchListSearch.tsx`
    - `frontend/src/components/research/GameResearchDetail.tsx`
    - `frontend/src/components/research/TrainingBatchDetail.tsx`
    - `frontend/src/components/research/VisualizationGallery.tsx`
    - `frontend/src/components/research/ExpandableJsonPanel.tsx`
    - `frontend/src/components/research/TrainingProgressBadge.tsx`
  - Keep `Research.tsx` as composition/glue that instantiates the presenter and passes view state to child components.

- [x] Expand the presenter/service boundaries.
  - Files: `frontend/src/presenters/ResearchPresenter.ts`, `frontend/src/service/ResearchService.ts`.
  - Presenter owns tab selection (`games` vs `training batches`), selected row, search query, sort mode, loading/error state, and WebSocket subscription lifecycle.
  - Service owns `fetchGameList`, `fetchGameDetail`, `fetchTrainingBatchList`, `fetchTrainingBatchDetail`, `startTrainingLoop`, and `subscribeToTrainingSessions`.
  - Move direct `fetch()` calls currently inside `Research.tsx` into `ResearchService`.

- [x] Build the left-column browser.
  - Tabs in the same left column: `Games` and `Training Batches`.
  - Search bar filters by id/name/ruleset/bot model where available.
  - Sort controls support time and name/id. Time sort should be newest-first by default.
  - Game rows show game id/name, created time, game type, and training batch/generation if applicable.
  - Training batch rows show batch id/name, status, started/completed time, ruleset, bot count, and generations.
  - In-progress training loops appear in the training batch list with a loading/spinner icon over or beside the name.
  - Hovering an in-progress row shows a tooltip with latest WebSocket progress: current game id, generation, generations left, population size, and latest fitness summary.

- [x] Build game detail display.
  - On selection, fetch full game detail by id.
  - Show visualization gallery first.
  - Show concise metadata summary: game id, created time, type, day/phase, ruleset if available, linked training batch/generation if available.
  - Move the parsed game data currently rendered inline in `Research.tsx` into an expandable hidden component.
  - Default raw/parsed data panel to collapsed; use pretty JSON or structured sections only after the researcher toggles it open.

- [x] Build training batch detail display.
  - On selection, fetch batch detail by id.
  - Show batch visualizations first.
  - Show linked games in generation order with quick links/select actions.
  - Show concise generation stats table below charts.
  - If batch is in progress, update status/progress from WebSocket without requiring a refresh.

- [x] Keep start-training functionality.
  - Continue using `NewGameModal` if it remains a good fit, but route all training start logic through `ResearchPresenter` and `ResearchService`.
  - After a loop starts, add the new in-progress batch/session to the training batch tab immediately from the POST response or next WebSocket event.
  - Avoid `alert()` for success/failure; use dashboard-local status messages so the researcher does not lose context.

- [x] Add frontend styling without breaking the rest of the app.
  - Existing styles are in `frontend/src/views/App.css` and `frontend/src/index.css`.
  - Prefer scoped research component class names over broad element selectors.
  - Make the layout usable at common laptop widths: fixed/minmax sidebar and scrollable details area.

## Phase 4: Tests and verification

- [ ] Backend verification.
  - Run targeted Python tests for DB provider changes and visualization command classes.
  - Run full backend test suite with `pytest` from repo root when implementation is complete.
  - Manually verify endpoints:
    - `GET /api/research/games`
    - `GET /api/research/games/{game_id}`
    - `GET /api/research/training-batches`
    - `GET /api/research/training-batches/{batch_id}`
    - `GET /api/research/visualizations/{visualization_id}`
    - `POST /api/research/train`
    - `/ws/research/training-sessions`

- [ ] Frontend verification.
  - Add presenter/service tests for search/sort, selection, detail loading, start-training success/failure, and WebSocket updates.
  - Run `npm run build` in `frontend/`.
  - Run `npm run lint` in `frontend/` after addressing any existing config issues.
  - Run `npm test` in `frontend/` if the existing Jest setup is operational.

- [ ] End-to-end research workflow check.
  - Start a training loop from the revamped page.
  - Confirm an in-progress training batch appears in the training batch tab with spinner/progress tooltip.
  - Confirm generated training games are linked to that batch and do not appear as ambiguous standalone human games.
  - Let at least one training game complete and confirm game visualizations are generated and served.
  - Let the batch complete and confirm batch visualizations are generated and served.
  - Select a human or human-bot game and confirm it appears in the game list and detail view without training metadata.
  - Toggle parsed game data open/closed and confirm the default detail view stays visualization-first.

## Suggested implementation order

- [x] 1. Add/adjust DTOs and write tests around expected API shapes.
- [x] 2. Add SQL/provider support for training batches and visualization metadata.
- [x] 3. Persist training batch lifecycle from the orchestrator.
- [x] 4. Add compact list/detail research endpoints.
- [x] 5. Add visualization command interfaces, registry, and storage/serving endpoints.
- [x] 6. Implement game visualization commands.
- [x] 7. Implement batch visualization commands.
- [x] 8. Refactor `ResearchService` and `ResearchPresenter` around the new APIs.
- [x] 9. Split the React research page into sidebar/detail/gallery/raw-data components.
- [x] 10. Rewire start-training and live progress into the new training batch list.
- [ ] 11. Run backend, frontend, and end-to-end verification.

Notes for future checklist updates:
- Add decisions directly under “Guiding decisions” when we settle open questions.
- Convert open questions into checked decisions rather than leaving stale ambiguity.
- If implementation discovers the existing game snapshot shape is missing trade/contest/development signals, add explicit data-capture tasks before expanding visualizations.
