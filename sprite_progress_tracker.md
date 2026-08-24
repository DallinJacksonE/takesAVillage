# Sprite Rework Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Replace the card-first gameplay page with a map-first, phase-aware village scene, animated player sprites, overlay action/chat panels, an accurate sticky status bar, safe player-facing state, and supported intent replacement behavior.

**Architecture:** Keep the existing React/TypeScript MVP boundary: WebSocket DTOs enter through `GameplayService`, `GameplayPresenter` owns connection/timer behavior, and route/components render state and dispatch presenter commands. Add an explicit backend human-client projection that separates private `me` data from public player visual data; derive a typed frontend scene model from that projection rather than embedding game rules in rendering components. Build sprite playback, scene placement, panel state, and notification playback as small independently tested units before assembling the new gameplay shell.

**Tech Stack:** Python 3/FastAPI/WebSocket backend, pytest, React 19, TypeScript 5.9, CSS Modules, Jest 30, React Testing Library, Vite.

---

## Decision status

The answers saved in `Spriterework.md` on 2026-08-19 are authoritative and are summarized below. Implementation may proceed in milestones, but must still stop at behavior that remains unanswered rather than silently selecting a branch.

### Resolved decisions

- Delivery is incremental. Milestone 1 establishes the map-first shell, responsive panel behavior, sticky status/timer foundation, and isometric axial-map presentation. Later milestones add WORK animation behavior, then TRADE, then NIGHT/end-of-day behavior. Player-triggered emoji reactions are in scope for a later milestone and are opened by right-clicking the local player's map sprite; the chosen emoji is public above that sprite for a few seconds.
- The UI is desktop-first and must also remain usable on laptops and mobile. On smaller screens, chat is a side overlay/toggle and phase actions become drawers beneath the map.
- Existing action workflows should be preserved where practical, but their cards/panels will be restyled for the game-first shell.
- WORK remains the backend-driven axial hex map using `MapTileDTO.q/r`, presented isometrically with Sunnyside art or placeholders. Hovering a tile containing a player shows player name and health; clicking a tile opens tile/map information. Players begin at one of their developments when available.
- Placeholder terrain/development tiles are acceptable until final art is selected. Useful bundled Sunnyside sprites, tiles, and props should be curated into stable application asset paths rather than referencing the source-pack directory directly.
- Chrome and Firefox are the initial browser targets. Prefer a simple CSS or canvas-mask approach for an approximately 3px player-color outline; escalate to a shader only if the simpler approaches cannot produce an acceptable result.
- Multiple players sharing an endpoint are assigned deterministic geometric slots: center for one, line endpoints for two, triangle vertices for three, square vertices for four, and corresponding regular-polygon points for larger groups.
- The backend is authoritative for a player's animation enum and map location so all clients see consistent animation/location/emoji state. The frontend maps backend hex/tile locations into rendered map coordinates.
- Human clients must not receive hidden `game_length`; the current `day` remains visible. A deliberately limited public-player projection is required for other players, while `me` retains approved private gameplay data.
- NIGHT hurt/death animation completion delays advancement into the next WORK day. Each affected human client acknowledges its own one-shot animation by transition ID; the server advances after every affected player acknowledges or after a five-second timeout. Training games retain immediate deterministic advancement.
- Deferred intent changes are made by clicking another still-valid opportunity; selecting it replaces the prior intent. A separate unlock button/command is not required for the stated UX. If a selected development becomes contested, the existing invalidation returns the player's goblin to one of their developments to idle until another choice is made.
- Immediate/irreversible actions include building, starting a contest, starting a fire, and execution of a trade once both parties have finalized it. Trade proposals/communications remain revocable before execution. Remaining contest-support and campfire-guest replacement edge cases must be covered when those phase milestones begin.
- A collapsed side panel receives an attention dot when its underlying state changes. Opening that panel marks the current information seen and clears the dot; no reload/reconnect persistence was requested.
- Animation targets 30 FPS with the rate represented by a central, easily changed setting and sprite playback derived from frame metadata.
- Sprite playback must advance left-to-right and use image dimensions/validated metadata rather than trusting a filename blindly. The malformed `spr_death_strip13.png` must not be treated as containing unavailable frames.

### Remaining decision needed

- Question 17 did not receive an answer: the timer transport remains undecided (absolute phase deadline, periodic server ticks, or reconciled snapshots), including whether the first minute displays `60`. Milestone 1 may build/test the sticky timer UI and exact orange-at-30/red-below-15 severity rules, but must not replace the transport protocol until this is answered.

### Curated asset inventory

- Existing goblin strips under `frontend/public/images/sprites/players/goblin/` use 96×64 frames: idle (9), watering (5), axe (10), mining (10), dig (13 over two rows), hammering (23 over three rows), and the inconsistent death file currently holding only nine visible frame cells.
- Copied from the bundled Sunnyside source pack into stable application paths for later animation milestones: `spr_walk_strip8.png`, `spr_carry_strip8.png`, and `spr_hurt_strip8.png`, each 768×64 with eight 96×64 frames.
- Copied scene-source sheets into `frontend/public/images/sprites/scenes/tilesets/`: `sunnyside-world-16px.png` (1024×1024) and `sunnyside-forest-32px.png` (320×576). Milestone 1 continues to use placeholder-colored hexes until exact atlas coordinates are selected.
- Curated the four-frame Sunnyside fire strip into the stable path `frontend/public/images/sprites/effects/campfire.png`; NIGHT host groups render it as an animated pixel-art campfire prop.
- Useful later source-pack candidates include the goblin attack strip and campfire/fire props, but the source goblin attack file is also dimensionally inconsistent with its `strip10` name and must be validated before curation.

### Implementation progress (2026-08-19)

- Milestone 1 is implemented: the gameplay route now uses a map-first shell, sticky player/day/phase/timer status, responsive action and chat overlays, and a compact isometric axial projection. The existing phase controls remain available in the action panel.
- Milestone 1 timer work intentionally stops at presentation. The status bar uses the agreed normal/orange/red thresholds, but the existing snapshot-reset transport remains in place pending the unanswered timer-authority decision.
- The public/private player-state boundary required before visual work is implemented. `player_list` now contains identity and public village state only; private resources, available work, actions, timeline, sickness chance, and committed action remain under `me`.
- Milestone 2 WORK presence and animation is implemented: server projections publish typed public animation/location state, the frontend renders every player on the map, map actors walk before beginning their authoritative activity animation, and immediate builds display hammering at their tile.
- Sprite playback now supports multi-row grids using explicit frame count and column metadata. The status-bar goblin uses the same authoritative activity as the local map actor. Farm, woods, mine, maintain/upgrade/build, contest, sick, and dead states have catalog mappings; malformed death metadata is capped at the nine actual frame cells.
- Follow-up visual feedback replaces the overly compressed map projection with standard pointy-top axial spacing (`x = size * √3 * (q + r/2)`, `y = size * 3/2 * r`) so adjacent hex edges interlock correctly. Player sprites are enlarged relative to the tile footprint.
- The chat overlay now reserves its full available height for chat, opens its channel rail expanded, wraps channel labels rather than truncating them, and shows a `MEMBERS` eyebrow containing every active-chat participant. The separate village roster is no longer duplicated above the live chat.
- Milestone 3 TRADE scene foundations are implemented. During TRADE the axial tiles are replaced by a placeholder forest clearing; accepted trade partners move to opposite sides of a shared meeting point, face each other, and use the curated carry strip. Fully finalized trades return both actors to their idle starting positions through the existing location transition.
- Simultaneous accepted trades receive deterministic, sorted clearing lanes so separate pairs do not overlap. The backend remains authoritative for the accepted trade ID and each player's initiator/target side.
- Milestone 4 NIGHT/end-of-day behavior is implemented. During NIGHT, the axial map is replaced by a dark clearing; hosts and their guests receive deterministic slots around a shared animated campfire, while cold players occupy a separate deterministic row. NIGHT resolution preserves those locations while projecting authoritative one-shot `HURT`/`DEAD` animations.
- Human games now pause at NIGHT resolution for affected-client animation acknowledgements. The backend publishes a typed transition ID/deadline/affected-player list, accepts acknowledgements only from affected players, and has a five-second server timeout so disconnected clients cannot stall the game. The frontend acknowledges after the local sprite metadata duration, including an immediate reduced-motion path. Sickness/death resolution also queues player-facing toast notifications.
- Milestone 5 public emoji reactions is implemented. Right-clicking the local map actor opens an accessible four-emoji menu (`👍`, `❤️`, `😂`, `😠`). The selected enum is validated and timestamped by the backend, broadcast in public player state, rendered above the actor, and expires after four seconds without locking or replacing the player's phase action.
- Phase action attention state is implemented for the map-first shell. Collapsed action panels now compare a focused phase-action signature rather than raw WebSocket snapshots, show a red update dot only when meaningful phase/action content changes while collapsed, ignore timer-only countdown ticks, and clear the dot when opened.
- The action panel attention crash caused by backend dictionary-shaped `map` payloads is fixed. The frontend DTO now reflects the existing backend contract (`MapDataDTO` is an array or tile-id dictionary), and attention/map-position code handles both shapes.
- The first responsive/accessibility acceptance follow-up is implemented: action/chat toggles now expose `aria-controls`, and open panels close on `Escape` while returning focus to their toggle.
- Map actor placement is adjusted so WORK/TILE actors anchor on their target tile instead of floating above it. NIGHT campfires now use deterministic regular-polygon fire anchors when multiple hosts exist; hosts move to their fire point and guests are slotted around their host's fire instead of every fire group overlapping at the clearing center.
- Reduced-motion acceptance now covers map actors: when `prefers-reduced-motion: reduce` is active, actors skip the transient WALK lead-in and render their authoritative activity immediately.
- Available WORK actions now display the target development and agreed wage inline with each Commit button, including an accessible button label that repeats that contract context.
- Campfire NIGHT UI now makes the instant-start rule explicit: hosts are told they stay at their own fire and cannot request/join another fire, while guests can switch to another host fire or leave their current host to start their own fire. Backend campfire reducers now remove guests from previous fires when they switch/start their own, while rejecting host attempts to join another fire.

### Handoff for the next implementation session

- The geometry correction is complete in `frontend/src/components/gameplay/mapGeometry.ts`. Keep the standard pointy-top axial projection; do not restore the former `1.05 * size` compressed row step. `frontend/test/map-geometry.test.ts` now protects the full-width horizontal neighbor step and the staggered half-width/three-quarter-height row step.
- Live browser QA was performed against a one-player in-memory game at a 1265×731 viewport. The three generated tiles shared their polygon edges/vertices without gaps or accidental overlap. The stronger map background initially lost to the global `.card` rule, so `VillageMap.module.css` intentionally uses the more specific `.card.mapCard` selector.
- Map actors now render at scale `1.35` and the local status-bar sprite at scale `1`. These values were chosen after live inspection because the first increase (`1.04`/`0.82`) still looked too small inside the 76px-tall hexes.
- Chat member data is carried by `ActiveChatViewModel.memberIds`. `null` means the global channel and resolves to every public player; group channels use the server-provided `member_ids`, which already include the creator. `ActiveChat.tsx` resolves those IDs through `getPlayerName` and renders the complete list under the `MEMBERS` eyebrow.
- The live chat now occupies the full chat overlay. Do not re-add `PlayerRoster` above `TabbedCommunicator`; it made the message window unnecessarily short and duplicated information now provided by the member eyebrow. `PlayerRoster` remains imported because it is still used by the dead-player view.
- The channel rail starts expanded and wraps long channel labels. At viewports up to 1420px its expanded width is constrained to `165–190px`, leaving enough width for message entry while retaining readable names.
- Focused coverage was added in `frontend/test/chat-view.test.ts` and `frontend/test/active-chat.test.tsx`. Final verification after all follow-up edits: 16 Jest suites / 32 tests passed, ESLint passed with zero warnings, the TypeScript/Vite production build passed, and `git -c core.whitespace=cr-at-eol diff --check` passed. No backend source changed during this follow-up, so backend tests were not rerun after the previously passing full backend suite.
- Continue with the remaining milestones in order. Preserve existing phase controls while replacing their presentation, keep public/private state separated, and do not implement authoritative timer transport until unanswered question 17 is resolved.
- NIGHT placement and delayed advancement are complete. The acknowledgement contract is `night_animation_complete` with a server-issued transition ID; only affected players count toward completion, and the server timeout remains authoritative. Preserve this affected-client-only contract unless requirements change.
- TRADE coverage now lives in `service/tests/game/test_state_serializer.py`, `frontend/test/phase-scene.test.ts`, `frontend/test/map-geometry.test.ts`, `frontend/test/map-player-actor.test.tsx`, and `frontend/test/player-sprite-metadata.test.ts`. Final verification for this increment: 267 backend tests passed (1 skipped, 11 subtests), 17 Jest suites / 38 tests passed, ESLint passed, the TypeScript/Vite production build passed, and `git -c core.whitespace=cr-at-eol diff --check` passed.
- NIGHT/emoji coverage now lives in `service/tests/game/test_phase_lifecycle.py`, `service/tests/game/test_state_serializer.py`, `service/tests/websocket/test_game_events.py`, `service/tests/game_manager/test_loop.py`, `frontend/test/night-scene.test.tsx`, `frontend/test/night-transition.test.tsx`, `frontend/test/map-geometry.test.ts`, `frontend/test/phase-scene.test.ts`, and `frontend/test/map-player-actor.test.tsx`. Timer-driven NIGHT resolution now drains the same notification queue as player-driven resolution. Final verification: 276 backend tests passed (1 skipped, 11 subtests), 19 Jest suites / 45 tests passed, ESLint passed with zero warnings, the TypeScript/Vite production build passed, and `git -c core.whitespace=cr-at-eol diff --check` passed.
- The next remaining plan work is responsive/accessibility/multiplayer acceptance for the sprite shell and action/chat panels. Authoritative timer transport remains blocked on unanswered question 17, and the human/agent `game_length` projection split should be audited before declaring the state-contract task complete.
- Panel attention coverage lives in `frontend/test/phase-attention.test.ts` and `frontend/test/gameplay-shell.test.tsx`. Final frontend verification for this increment: 20 Jest suites / 49 tests passed, ESLint passed with zero warnings, and the TypeScript/Vite production build passed.
- The latest follow-up adds regression coverage for backend dictionary-shaped maps in `frontend/test/phase-attention.test.ts` and Escape/focus behavior in `frontend/test/gameplay-shell.test.tsx`. Final frontend verification: 20 Jest suites / 51 tests passed, ESLint passed with zero warnings, and the TypeScript/Vite production build passed.
- Placement coverage was extended in `frontend/test/map-geometry.test.ts` and `frontend/test/night-scene.test.tsx` for corrected WORK actor anchoring and multiple simultaneous NIGHT fire groups. Final frontend verification: 20 Jest suites / 53 tests passed, ESLint passed with zero warnings, the TypeScript/Vite production build passed, and `git -c core.whitespace=cr-at-eol diff --check` passed.
- Reduced-motion actor coverage lives in `frontend/test/map-player-actor.test.tsx`. Final frontend verification: 20 Jest suites / 54 tests passed, ESLint passed with zero warnings, and the TypeScript/Vite production build passed.
- Available-work coverage lives in `frontend/test/available-work-card.test.tsx`, campfire UI coverage lives in `frontend/test/campfire-ring.test.tsx`, and backend host/guest campfire behavior coverage lives in `service/tests/game/test_actions.py` plus `service/tests/game/test_contracts.py`. Final verification: 22 Jest suites / 57 tests passed, ESLint passed with zero warnings, the TypeScript/Vite production build passed, and backend pytest passed with 279 tests, 1 skipped, 1 warning, and 11 subtests.

## Current codebase context

- `frontend/src/views/Gameplay.tsx` is a 433-line route component containing presenter setup, connection/toast UI, lobby/death screens, header, phase routing, map, roster, chat, and finish controls. The rework should decompose this file rather than adding more inline UI.
- `frontend/src/components/gameplay/VillageMap.tsx` renders draggable/zoomable axial hexes using colors and Font Awesome icons. It has no player layer or phase scene abstraction.
- `frontend/src/components/gameplay/player/PlayerSprite/PlayerSprite.tsx` and its CSS only animate a single horizontal row. The current `steps(frameCount)` animation cannot traverse strips with more than ten columns.
- `frontend/src/components/gameplay/player/playerSpriteCatalog.ts` catalogs only idle, hammer, and mining. Curated assets also include axe, death, dig, and watering; required walk/carry/sleep/hurt/contest/fire assets are unresolved.
- `spr_death_strip13.png` has room for only nine 96×64 frames, so asset validation must reject or explicitly override inconsistent metadata.
- `service/game/serializers/state.py` serializes every player with `Player.to_dict()`, exposing resources, actions, timeline, available work, and committed action to every client. It also sends `game_length` even though `GameStateDTO` does not declare it.
- `service/game/game.py:get_time_remaining()` floors the remaining duration, while `GameplayPresenter` starts a separate one-second local interval and resets it whenever a state snapshot arrives.
- The backend supports `Game.clear_intent()` internally but `service/game/packet_handling/registry.py` has no client command for replacing an intent.
- The frontend has no gameplay/sprite tests. Existing Jest infrastructure in `frontend/jest.config.json` supports component and pure TypeScript tests.

## Proposed delivery order

1. Freeze decisions and asset metadata.
2. Harden and test the backend client contract.
3. Add timer synchronization, intent replacement, and one-shot visual notifications.
4. Build/test the sprite and scene-model foundations.
5. Build the map-first shell and sticky status bar.
6. Add WORK, TRADE, and NIGHT scenes incrementally.
7. Integrate panels, attention state, toasts, and observation mode.
8. Run automated, responsive, accessibility, and multiplayer acceptance checks.

---

### Task 1: Resolve requirements and inventory assets

**Objective:** Turn the questions in `Spriterework.md` into explicit acceptance criteria and a validated asset manifest before code changes.

**Files:**
- Modify: `Spriterework.md`
- Modify: `.hermes/plans/2026-08-19_113240-sprite-rework.md`
- Inspect: `frontend/public/images/sprites/players/goblin/*.png`
- Inspect: `frontend/public/images/sprites/Sunnyside_World_ASSET_PACK_V2.1/**`

**Steps:**

1. Record an answer under every numbered question in `Spriterework.md`; do not silently infer unanswered behavior.
2. Copy the answers into “Resolved decisions” above in implementation-oriented terms.
3. Inventory every selected image with path, pixel dimensions, frame dimensions, frame count, columns, rows, FPS, loop/one-shot behavior, and intended game activity.
4. Repair or replace inconsistent source images (especially `spr_death_strip13.png`) or document a deliberate metadata override.
5. Define phase-scene acceptance screenshots/wireframes for WORK, TRADE, and NIGHT at each supported viewport.
6. Define observable acceptance examples for intent replacement, attention dots, timer thresholds, sickness/death effects, reconnects, and reduced motion.

**Verification:** Every activity and scene named in the rework has an asset/fallback and state trigger; every question is answered; no implementation task below retains an unresolved branch.

---

### Task 2: Introduce a safe human-client state contract

**Objective:** Stop sending private/research data for other players while exposing only the public visual facts required by the map.

**Files:**
- Modify: `service/game/serializers/state.py`
- Modify: `service/game/models/player.py` only if reusable private/public serializers belong on the model
- Modify: `service/tests/test_state_builder.py`
- Modify: `frontend/src/dtos/index.ts`
- Test: `service/tests/test_state_builder.py`

**Steps:**

1. Add failing serializer tests with two players proving that `me` retains approved private fields while each `player_list` entry contains exactly the approved public keys.
2. Add a failing test proving that human WebSocket state omits `game_length` if question 10 confirms that meaning; retain training/agent fitness data through its existing research/bot projection rather than leaking it to human clients.
3. Add tests for public activity/intent fields selected in question 11, including a player with no activity and a dead/sick player.
4. Run `python3 -m pytest service/tests/test_state_builder.py -q` and confirm the tests fail against the current `Player.to_dict()` list serialization.
5. Implement explicit serializer helpers (for example private-player and public-player projections) in `service/game/serializers/state.py`; do not filter arbitrary `to_dict()` output with a blacklist.
6. Update `GameStateDTO` and split the existing `PlayerDTO` into private and public DTOs if their shapes differ. Update component props/hooks that only need public identity/status to use the narrow type.
7. Run the focused backend test and `cd frontend && npm run build`.

**Expected result:** A player cannot inspect another player's resources, private actions/contracts, timeline, private work offers, sickness probability, or other fields not explicitly approved; map-required identity, health, location/activity, and public fire/contest state remain available.

---

### Task 3: Make timer synchronization authoritative and testable

**Objective:** Display a smooth, reconnect-safe timer with the exact agreed rounding and warning thresholds.

**Files:**
- Modify: `service/game/serializers/state.py`
- Modify: `service/game/game.py` if the selected protocol requires an absolute phase deadline
- Modify: `frontend/src/dtos/index.ts`
- Modify: `frontend/src/presenters/GameplayPresenter.ts`
- Create: `frontend/test/gameplay-presenter.test.ts`
- Modify: `service/tests/test_state_builder.py`

**Steps:**

1. Write presenter tests using fake timers for initial state, one-second countdown, a later state update, phase transition, reconnect/disconnect, zero clamping, and destruction/interval cleanup.
2. Add backend contract tests for the selected protocol:
   - Absolute deadline option: serialize one server timestamp/deadline and calculate display time from it.
   - Periodic remaining-time option: test broadcast cadence and reconciliation tolerance.
3. Run the focused Jest and pytest tests and confirm the current local-only timer behavior fails the synchronization cases.
4. Implement the selected protocol without maintaining two competing authoritative counters.
5. Extract a pure timer-severity formatter used by the sticky bar; test normal, orange-at-threshold, red-below-threshold, zero, and minute-boundary rendering.
6. Verify reconnect immediately requests/reconciles current phase timing and stale packets cannot move the timer backward beyond the agreed tolerance.

**Commands:**
- `python3 -m pytest service/tests/test_state_builder.py -q`
- `cd frontend && npm test -- --runInBand gameplay-presenter.test.ts`

**Expected result:** The minute boundary and `<=30`/`<15` styling match the answered specification, the display reaches zero without going negative, and reconnects do not leave a stale countdown.

---

### Task 4: Add legal intent replacement end to end

**Objective:** Let players replace only the agreed deferred intents while preserving irreversible immediate actions and dependency locks.

**Files:**
- Create: `service/game/packet_handling/intents.py`
- Modify: `service/game/packet_handling/registry.py`
- Modify: `service/game/state/legal_actions.py`
- Modify: `service/game/game.py` only if dependency queries belong on the aggregate
- Modify: `service/tests/game/test_actions.py`
- Modify: `service/tests/game/test_projections.py`
- Modify: `service/tests/game/test_intents_and_contests.py`
- Modify: `frontend/src/dtos/index.ts`
- Modify: `frontend/src/presenters/GameplayPresenter.ts`
- Create: `frontend/test/gameplay-presenter.test.ts` or extend the file created in Task 3

**Steps:**

1. Add parameterized backend tests for every approved replaceable intent and every forbidden immediate/dependency-locked action.
2. Add tests that replacement restores `phase_state` to `NEEDS_REPLACEMENT`, clears `committed_action`, and exposes the correct legal actions without refunding or rolling back immediate effects.
3. Add race tests where another player's dependent commitment arrives first; the command must reject atomically and preserve the original intent.
4. Add projection tests proving the replacement command appears only when currently legal.
5. Register the selected command name in `COMMAND_HANDLERS` and `PHASE_LOCK_ALLOWED_COMMANDS`, and implement a command that delegates to authoritative game legality before calling `clear_intent()`.
6. Add a typed presenter method and payload; test its emitted WebSocket envelope.
7. Do not add optimistic client mutation. Wait for the authoritative broadcast before moving the sprite or reopening choices.

**Commands:**
- `python3 -m pytest service/tests/game/test_actions.py service/tests/game/test_projections.py service/tests/game/test_intents_and_contests.py -q`
- `cd frontend && npm test -- --runInBand gameplay-presenter.test.ts`

**Expected result:** Replacing an allowed intent is deterministic and race-safe; immediate actions cannot be undone; the client renders legality from the server contract.

---

### Task 5: Add explicit one-shot visual events and health notifications

**Objective:** Distinguish persistent scene state from events that must animate/toast exactly once.

**Files:**
- Modify: `service/game/state/events.py`
- Modify: `service/game/state/phase_resolution.py` and/or `service/game/packet_handling/phase_resolution.py` according to the selected event boundary
- Modify: `service/api/websocket/game_events.py`
- Modify: `service/api/websocket/connection_manager.py` if phase-resolution events require broadcast delivery
- Modify: `service/tests/game/test_phase_resolution.py`
- Modify: `service/tests/websocket/test_game_events.py`
- Modify: `frontend/src/service/GameplayService.ts`
- Modify: `frontend/src/presenters/GameplayPresenter.ts`
- Modify: `frontend/src/dtos/index.ts`

**Steps:**

1. Add backend tests for healthy→sick, sick→dead, sick→recovering, and recovering→healthy transitions, asserting exactly the agreed recipients and event payloads.
2. Include stable event IDs/sequence information if events can be replayed after reconnect; test deduplication semantics.
3. Add service parsing tests for the selected visual-event WebSocket event and typed payload.
4. Add presenter tests proving one-shot events reach the view once while persistent state updates remain idempotent.
5. Emit health/toast events from authoritative NIGHT resolution, not by comparing mutable frontend snapshots alone.
6. Preserve current state broadcasting after event delivery so clients finish on the authoritative state.

**Expected result:** Damage/death/recovery animations and sickness/death toasts do not disappear between snapshots, duplicate on unrelated broadcasts, or leak private notifications beyond their approved audience.

---

### Task 6: Replace horizontal-only sprite playback with validated grid playback

**Objective:** Correctly animate sprite sheets of 1–N rows, support looping/one-shot playback and reduced motion, and reject impossible metadata.

**Files:**
- Modify: `frontend/src/components/gameplay/player/PlayerSprite/types.ts`
- Modify: `frontend/src/components/gameplay/player/PlayerSprite/PlayerSprite.tsx`
- Modify: `frontend/src/components/gameplay/player/PlayerSprite/PlayerSprite.module.css`
- Modify: `frontend/src/components/gameplay/player/playerSpriteCatalog.ts`
- Create: `frontend/src/components/gameplay/player/PlayerSprite/spriteFrames.ts`
- Create: `frontend/test/player-sprite.test.tsx`
- Create: `frontend/test/sprite-frames.test.ts`
- Add/replace selected files under: `frontend/public/images/sprites/players/goblin/`

**Steps:**

1. Write pure tests for `frameIndex -> {column,row,x,y}` across 5, 9, 10, 13, and 23 frames with ten columns per full row and a partial final row.
2. Write validation tests for positive dimensions/FPS, sufficient image cells, explicit column overrides, and the malformed death strip policy selected in question 19.
3. Write component tests for loop, one-shot completion callback, pause, left/right direction, scale, accessible label, and reduced-motion first/representative frame.
4. Run the tests and verify the current single-row CSS implementation fails 13/23-frame cases.
5. Implement frame selection using a deterministic frame clock and explicit X/Y background offsets; do not stretch the entire sheet with `background-size: auto 100%`.
6. Keep movement transform separate from sprite-facing/scale transform so positioning does not overwrite animation transforms.
7. Expand the catalog to every approved activity with explicit metadata; do not parse production behavior solely from filenames, though a validation helper may check filename metadata against the catalog.
8. Test image loading failure behavior and fallback to idle/placeholder.

**Command:** `cd frontend && npm test -- --runInBand sprite-frames.test.ts player-sprite.test.tsx`

**Expected result:** Hammering 23 and dig 13 traverse rows correctly; one-shot animations terminate on the intended frame; invalid catalog metadata fails tests/build rather than silently showing the wrong frames.

---

### Task 7: Build a pure phase-to-scene view-model layer

**Objective:** Convert approved public game state and one-shot events into deterministic scene, placement, movement, and sprite instructions without coupling those rules to React layout.

**Files:**
- Create: `frontend/src/components/gameplay/scene/types.ts`
- Create: `frontend/src/components/gameplay/scene/buildScene.ts`
- Create: `frontend/src/components/gameplay/scene/sceneAnchors.ts` or selected authored map data file
- Create: `frontend/test/gameplay-scene.test.ts`
- Modify: `frontend/src/dtos/index.ts`

**Steps:**

1. Define typed scene output: phase backdrop, sky/theme, development anchors, player start/target positions, facing direction, persistent activity, queued one-shot activity, label/color, and z-order.
2. Write table-driven WORK tests for idle, each development work type, build/maintain/upgrade, contest initiation/support/defense, sick sleeping, and dead players.
3. Write TRADE tests for unpaired players, accepted trade approach/carry, finalized return, simultaneous trades, cancellation, and fallback placement.
4. Write NIGHT tests for hosts, guests, cold/alone players, fire capacity, sickness/hurt, death, and phase transition.
5. Add deterministic slotting tests for multiple players sharing one anchor and stable ordering across state packet order changes.
6. Add tests for missing/unknown activity, missing development, malformed public data, and reconnect directly into a mid-phase state.
7. Implement only mappings explicitly backed by the resolved state contract.

**Command:** `cd frontend && npm test -- --runInBand gameplay-scene.test.ts`

**Expected result:** Identical authoritative state produces identical scene instructions; React components do not inspect contract internals to decide game semantics.

---

### Task 8: Create the map-first responsive gameplay shell and sticky status bar

**Objective:** Establish the new page hierarchy before adding phase-specific animation details.

**Files:**
- Modify: `frontend/src/views/Gameplay.tsx`
- Modify: `frontend/src/views/Gameplay.module.css`
- Create: `frontend/src/components/gameplay/layout/GameplayShell.tsx`
- Create: `frontend/src/components/gameplay/layout/GameplayShell.module.css`
- Create: `frontend/src/components/gameplay/layout/PlayerStatusBar.tsx`
- Create: `frontend/src/components/gameplay/layout/PlayerStatusBar.module.css`
- Create: `frontend/src/components/gameplay/layout/SidePanel.tsx`
- Create: `frontend/src/components/gameplay/layout/SidePanel.module.css`
- Create: `frontend/test/player-status-bar.test.tsx`
- Create: `frontend/test/gameplay-shell.test.tsx`

**Steps:**

1. Add status-bar tests for player name/color sprite, phase/day display per question 10, centered monospace timer, threshold classes, connection state, and dead/observer state.
2. Add shell tests for left action panel, central map scene, right chat panel, expand/collapse controls, keyboard focus, ARIA labels, and the resolved narrow-screen behavior.
3. Move connection and toast rendering out of nested functions in `Gameplay.tsx` into stable components.
4. Preserve presenter construction/destruction and lobby/ended routing while replacing only the active gameplay layout.
5. Implement CSS grid/overlay regions with the map as the viewport-filling primary layer and the status bar `position: sticky` or `fixed` according to acceptance criteria.
6. Ensure open panels constrain/overlay the map as selected without introducing document scroll that hides the status bar.
7. Keep the small status-bar goblin bound to the same scene activity resolver as the map goblin, with an explicit compact scale/viewport.

**Commands:**
- `cd frontend && npm test -- --runInBand player-status-bar.test.tsx gameplay-shell.test.tsx`
- `cd frontend && npm run build`

---

### Task 9: Upgrade the village map into a layered scene renderer

**Objective:** Render selected terrain/development art and moving player sprites over the authoritative axial map while preserving build selection and pan/zoom.

**Files:**
- Modify or split: `frontend/src/components/gameplay/VillageMap.tsx`
- Modify: `frontend/src/components/gameplay/VillageMap.module.css`
- Create: `frontend/src/components/gameplay/scene/SceneViewport.tsx`
- Create: `frontend/src/components/gameplay/scene/DevelopmentLayer.tsx`
- Create: `frontend/src/components/gameplay/scene/PlayerLayer.tsx`
- Create: `frontend/src/components/gameplay/scene/PlayerActor.tsx`
- Create: `frontend/test/village-map.test.tsx`
- Create: `frontend/test/player-actor.test.tsx`
- Add selected terrain/development assets under: `frontend/public/images/sprites/`

**Steps:**

1. Add tests that map tile coordinates produce stable anchors and that clicking an open tile still opens the build affordance without firing after a drag.
2. Add actor tests for start→walk→target-activity sequencing, direction changes, interrupted targets, same-target updates, one-shot event precedence, and reduced motion.
3. Separate viewport pan/zoom transforms from actor movement and sprite transforms.
4. Render layers in a fixed order: backdrop/sky, terrain, developments/props, fires/trade props, player shadows/actors, selection/action overlays.
5. Implement the selected movement model and deterministic endpoint slotting from Task 7.
6. Apply player outlines using the selected technique and stable server/client color source.
7. Preserve map build callback behavior and make selection controls keyboard-operable.
8. Add cleanup tests for animation timers/listeners on unmount and phase changes.

**Expected result:** WORK is playable from the map-first shell and player sprites visibly move to stable action locations without breaking map interaction.

---

### Task 10: Integrate phase action panels and attention state

**Objective:** Rehome existing WORK/TRADE/NIGHT controls into the left panel and chat into the right panel without changing gameplay semantics accidentally.

**Files:**
- Create: `frontend/src/components/gameplay/layout/PhaseActionPanel.tsx`
- Create: `frontend/src/components/gameplay/layout/phaseAttention.ts`
- Modify: `frontend/src/components/gameplay/DevelopmentsCard.tsx`
- Modify: `frontend/src/components/gameplay/AvailableWorkCard.tsx`
- Modify: `frontend/src/components/gameplay/trading/TradeDesk.tsx`
- Modify: `frontend/src/components/gameplay/CampfireRing.tsx`
- Modify: `frontend/src/components/gameplay/communication/TabbedCommunicator.tsx`
- Modify: associated CSS Modules only as needed
- Create: `frontend/test/phase-action-panel.test.tsx`
- Create: `frontend/test/phase-attention.test.ts`

**Steps:**

1. Write pure tests for every resolved attention trigger and clear/persistence rule.
2. Write panel tests proving only the current phase controls render, pending responses remain accessible while an intent is submitted, and replacement controls appear only when legal.
3. Remove direct `finished_phase` guesses where the new legal-action/phase-state projection is authoritative.
4. Reuse existing action callbacks and forms first; perform interaction redesign only where Task 1 explicitly approved it.
5. Bind the red dot to tested attention state, not to every WebSocket snapshot.
6. Keep chat unread handling independent from phase attention unless the resolved requirements explicitly combine them.
7. Preserve focus when panels expand/collapse and return focus to the toggle when closing.

**Expected result:** Existing actions remain reachable and correctly enabled in the new shell; attention indicators are meaningful and clear predictably.

---

### Task 11: Complete TRADE and NIGHT scene behavior

**Objective:** Add phase-specific clearings, trade/campfire actor sequences, end-of-day effects, and matching status-bar sprites.

**Files:**
- Modify: `frontend/src/components/gameplay/scene/buildScene.ts`
- Modify: `frontend/src/components/gameplay/scene/SceneViewport.tsx`
- Modify: `frontend/src/components/gameplay/scene/PlayerActor.tsx`
- Modify: `frontend/src/components/gameplay/player/playerSpriteCatalog.ts`
- Add selected clearing/sky/campfire assets under: `frontend/public/images/sprites/`
- Extend: `frontend/test/gameplay-scene.test.ts`
- Extend: `frontend/test/player-actor.test.tsx`
- Create: `frontend/test/gameplay-notifications.test.tsx`

**Steps:**

1. Implement the TRADE clearing and tested approach/carry/stop/return sequence from authoritative trade state/events.
2. Implement the NIGHT clearing/lighting and host/guest/cold placements with fire props.
3. Queue hurt/death one-shots according to the selected phase-transition timing, then settle on persistent sick/dead state.
4. Connect sickness/death notifications to the extracted toast stack and verify event deduplication.
5. Mirror each local player's resolved activity in the compact status-bar sprite without duplicating event consumption.
6. Add reduced-motion behavior that immediately places actors at targets and presents state/toasts without motion-dependent information loss.
7. If approved as in-scope, add unhappy trade emoji as a separately tested one-shot event; otherwise leave it out.

---

### Task 12: Preserve waiting, ended, dead-observer, reconnect, and error flows

**Objective:** Ensure the visual rework does not regress non-happy-path gameplay states.

**Files:**
- Modify: `frontend/src/views/Gameplay.tsx`
- Modify: `frontend/src/views/Gameplay.module.css`
- Create: `frontend/test/gameplay-view.test.tsx`
- Modify: `frontend/src/service/GameplayService.ts`
- Modify: `frontend/src/presenters/GameplayPresenter.ts`

**Steps:**

1. Add route-level tests for loading, waiting host/non-host, active, disconnected/reconnecting, ended, and dead observer states.
2. Verify presenter and WebSocket cleanup on route unmount and game ID changes.
3. Render dead players in observer mode with no action controls but retain approved map/chat/roster visibility.
4. Ensure direct reconnect into WORK/TRADE/NIGHT constructs the correct final scene without requiring missed historical packets.
5. Replace `alert()`-only gameplay errors with the approved accessible notification treatment if included in Task 1 decisions.
6. Remove development-only `console.log(gameState)` and remaining superseded inline layout styles from `Gameplay.tsx`.

---

### Task 13: Automated contract, unit, integration, and build verification

**Objective:** Prove backend and frontend behavior together before visual acceptance.

**Files:**
- Modify tests discovered above as failures reveal contract gaps
- Do not modify unrelated research/bot behavior unless the new client projection requires an explicit shared-contract adjustment

**Steps:**

1. Run focused backend tests after each backend task.
2. Run the entire backend suite: `python3 -m pytest -q`.
3. Run frontend tests serially for stable fake-timer/animation behavior: `cd frontend && npm test -- --runInBand`.
4. Run strict lint: `cd frontend && npm run lint`.
5. Run production type-check/build: `cd frontend && npm run build`.
6. Inspect test coverage for new pure logic (`spriteFrames`, scene builder, attention, timer) and add branch cases for uncovered state transitions.
7. Verify no human-client packet contains forbidden fields by capturing representative two-player `game_state` payloads in an automated WebSocket test.
8. Verify no new generated build/coverage files are accidentally tracked.

**Expected result:** All pytest/Jest tests, lint, and Vite production build pass with no warnings promoted to errors.

---

### Task 14: Multiplayer visual and accessibility acceptance

**Objective:** Validate the experience under realistic phase transitions and supported viewports, not only isolated tests.

**Files:**
- Update: `Spriterework.md` with an acceptance checklist/results section
- Optionally create screenshots under an agreed non-production test-artifact location; do not commit generated artifacts unless requested

**Steps:**

1. Start the backend/frontend using the project’s documented local or Docker workflow.
2. Join with enough clients/bots to exercise overlapping workers, a contest, a completed trade, multiple campfires, a cold player, sickness, and death.
3. Verify each client receives only its private state plus approved public state for others.
4. Verify timer behavior through a full minute boundary, action broadcasts, phase transitions, tab backgrounding, disconnect, and reconnect.
5. Verify map movement/placement and panel behavior at every supported viewport and browser selected in Task 1.
6. Verify keyboard-only panel/chat/action navigation, visible focus, labels/status announcements, color contrast, and `prefers-reduced-motion`.
7. Profile animation with the maximum supported player count; confirm the agreed FPS/frame-time and no accumulating timers/listeners.
8. Record pass/fail evidence against every acceptance criterion in `Spriterework.md`; fix failures at their owning layer and rerun all affected automated checks.

## Likely files changed

Backend:
- `service/game/serializers/state.py`
- `service/game/game.py`
- `service/game/models/player.py` (only if serializer ownership is intentionally changed)
- `service/game/state/events.py`
- `service/game/state/legal_actions.py`
- `service/game/packet_handling/intents.py`
- `service/game/packet_handling/registry.py`
- `service/game/packet_handling/phase_resolution.py`
- `service/api/websocket/game_events.py`
- `service/api/websocket/connection_manager.py`
- Focused tests under `service/tests/`

Frontend:
- `frontend/src/dtos/index.ts`
- `frontend/src/service/GameplayService.ts`
- `frontend/src/presenters/GameplayPresenter.ts`
- `frontend/src/views/Gameplay.tsx`
- `frontend/src/views/Gameplay.module.css`
- `frontend/src/components/gameplay/VillageMap.tsx`
- `frontend/src/components/gameplay/VillageMap.module.css`
- `frontend/src/components/gameplay/player/PlayerSprite/*`
- `frontend/src/components/gameplay/player/playerSpriteCatalog.ts`
- New `frontend/src/components/gameplay/layout/*`
- New `frontend/src/components/gameplay/scene/*`
- Existing phase cards/chat and their CSS Modules only where required to fit the panel shell
- New Jest tests under `frontend/test/`
- Selected assets under `frontend/public/images/sprites/`

## Risks and controls

- **Requirements ambiguity:** Do not begin implementation before Task 1; unresolved behavior is already documented in `Spriterework.md`.
- **Information leakage:** Use allowlisted public/private serializers and exact-key tests, not omission by frontend typing.
- **Bot/training regression:** Keep bot/research decision projections separate from the hardened human-client WebSocket projection; `game_length` currently has an explicit fitness-context test.
- **Animation/state drift:** Persistent position/activity comes from snapshots; one-shot effects come from typed, deduplicated events; neither is inferred from DOM history.
- **Race conditions when replacing intent:** Backend legality is authoritative and atomic; no optimistic clearing.
- **Sprite-sheet inconsistency:** Validate catalog metadata and source dimensions before rendering; malformed strips fail clearly or use an approved override.
- **Transform conflicts:** Separate viewport, actor movement, direction/scale, and frame-offset layers.
- **Performance:** Use one shared scene clock or CSS where valid, avoid one unmanaged interval per sprite, and test the maximum approved player count.
- **Scope creep:** Preserve existing action workflows unless Task 1 explicitly approves redesign; phase delivery should remain independently shippable.
- **Accessibility:** Reduced motion must preserve information; color outlines/dots require textual or semantic equivalents.

## Stop conditions

- Do not commit, push, or open a pull request unless the user separately requests it.
- Stop and ask rather than choosing an unanswered branch from `Spriterework.md`.
- A milestone is complete only when its focused tests pass and the relevant multiplayer acceptance case has been exercised.
