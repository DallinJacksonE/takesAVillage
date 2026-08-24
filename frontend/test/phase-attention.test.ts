import { buildPhaseAttentionKey, updatePanelAttention } from "../src/components/gameplay/layout/phaseAttention";
import type { GameStateDTO } from "../src/dtos";

const makeState = (overrides: Partial<GameStateDTO> = {}): GameStateDTO => ({
  status: "ACTIVE",
  is_host: false,
  host_connected: true,
  day: 1,
  phase: "WORK",
  time_remaining: 59,
  player_list: [],
  map: [],
  developments: [],
  chat_messages: [],
  chats: [],
  development_costs: {},
  max_fire_seats: 3,
  campfire_cost: { food: 0, iron: 0, wood: 1 },
  cold_sickness_rate: 0.25,
  hunger_sickness_rate: 0.25,
  recovery_rate: 0.25,
  training: false,
  me: {
    id: "player-1",
    name: "Moss",
    health: "healthy",
    sickness_chance: 0,
    fire_status: "COLD",
    fire_guests: [],
    resources: { food: 1, iron: 0, wood: 2 },
    developments: [],
    available_work: [],
    committed_action: null,
    actions: [],
    timeline: [],
    finished_phase: false,
    phase_state: "ACTIVE",
  },
  ...overrides,
});

describe("phase attention", () => {
  it("does not mark the initial collapsed panel as unread", () => {
    const key = buildPhaseAttentionKey(makeState());

    const state = updatePanelAttention(undefined, { isOpen: false, contentKey: key });

    expect(state.hasAttention).toBe(false);
  });

  it("marks a collapsed panel when phase-action content changes and clears when opened", () => {
    const initialKey = buildPhaseAttentionKey(makeState());
    const changedKey = buildPhaseAttentionKey(
      makeState({
        me: {
          ...makeState().me,
          available_work: [
            {
              action_id: "job-1",
              employer_id: "player-2",
              wage: 1,
              wage_type: "food",
              development: {
                id: "dev-1",
                type: "Farm",
                level: 1,
                maintenance_days: 3,
                owner_id: "player-2",
                maintenance_cost: {},
                upgrade_cost: {},
                can_upgrade: false,
                pending_contest: false,
              },
            },
          ],
        },
      }),
    );

    const closed = updatePanelAttention(undefined, { isOpen: false, contentKey: initialKey });
    const unread = updatePanelAttention(closed, { isOpen: false, contentKey: changedKey });
    const opened = updatePanelAttention(unread, { isOpen: true, contentKey: changedKey });

    expect(unread.hasAttention).toBe(true);
    expect(opened.hasAttention).toBe(false);
  });

  it("ignores timer-only updates so routine countdown ticks do not create attention", () => {
    const closed = updatePanelAttention(undefined, {
      isOpen: false,
      contentKey: buildPhaseAttentionKey(makeState({ time_remaining: 59 })),
    });

    const ticked = updatePanelAttention(closed, {
      isOpen: false,
      contentKey: buildPhaseAttentionKey(makeState({ time_remaining: 58 })),
    });

    expect(ticked.hasAttention).toBe(false);
  });

  it("accepts the backend map dictionary shape when building the attention key", () => {
    const key = buildPhaseAttentionKey(
      makeState({
        map: {
          "tile-1": {
            id: "tile-1",
            q: 0,
            r: 0,
            type: "Farm",
          },
        },
      } as Partial<GameStateDTO>),
    );

    expect(key).toContain("tile-1");
  });
});
