import { fireEvent, render, screen } from "@testing-library/react";
import CampfireRing from "../src/components/gameplay/CampfireRing";
import { PlayerProvider } from "../src/components/hooks/usePlayerName";
import type { CampfireActionDTO, GameStateDTO, PlayerDTO, PublicPlayerDTO } from "../src/dtos";

const publicPlayer = (
  id: string,
  name: string,
  fire_status: PublicPlayerDTO["fire_status"],
  fire_guests: string[] = [],
): PublicPlayerDTO => ({
  id,
  name,
  health: "healthy",
  fire_status,
  fire_guests,
  developments: [],
  finished_phase: false,
  phase_state: "ACTIVE",
  visual_state: {
    animation: fire_status === "HOST" ? "SICK" : "IDLE",
    location: fire_status === "HOST" ? { kind: "FIRE", id, slot: 0 } : { kind: "HOME" },
  },
});

const playerDto = (
  player: PublicPlayerDTO,
  actions: CampfireActionDTO[] = [],
): PlayerDTO => ({
  ...player,
  sickness_chance: 0,
  resources: { food: 1, wood: 2, iron: 0 },
  available_work: [],
  committed_action: null,
  actions,
  timeline: [],
});

const makeState = (
  me: PlayerDTO,
  player_list: PublicPlayerDTO[],
): GameStateDTO => ({
  status: "ACTIVE",
  state_revision: 1,
  is_host: true,
  host_connected: true,
  me,
  day: 1,
  phase: "NIGHT",
  time_remaining: 60,
  player_list,
  public_interactions: [],
  map: [],
  developments: [],
  chat_messages: [],
  chats: [],
  development_costs: {},
  max_fire_seats: 3,
  campfire_cost: { food: 0, wood: 1, iron: 0 },
  cold_sickness_rate: 0.3,
  hunger_sickness_rate: 0.5,
  recovery_rate: 0.2,
  training: false,
});

describe("CampfireRing", () => {
  it("tells hosts they stay at their own instant fire and hides join/start controls", () => {
    const moss = publicPlayer("player-1", "Moss", "HOST", []);
    const fern = publicPlayer("player-2", "Fern", "HOST", []);
    const state = makeState(playerDto(moss), [moss, fern]);

    render(
      <PlayerProvider players={[moss, fern]}>
        <CampfireRing
          state={state}
          onAccept={jest.fn()}
          onDeny={jest.fn()}
          onOfferSeat={jest.fn()}
          onRequestSeat={jest.fn()}
          onStartFire={jest.fn()}
        />
      </PlayerProvider>,
    );

    expect(screen.getByText("Hosting your own fire. Starting a fire is instant, so you will stay here for the night unless you end the day cold later.")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Request Seat/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /Start Fire/i })).toBeNull();
  });

  it("lets guests switch fires or leave their current fire to start their own", () => {
    const fern = publicPlayer("player-1", "Fern", "HOST", ["player-2"]);
    const moss = publicPlayer("player-2", "Moss", "GUEST", []);
    const ash = publicPlayer("player-3", "Ash", "HOST", []);
    const requestSeat = jest.fn();
    const startFire = jest.fn();
    const actions: CampfireActionDTO[] = [{
      id: "fire-1",
      initiator_id: moss.id,
      target_id: fern.id,
      status: "ACCEPTED",
      type: "CAMPFIRE",
      is_request: true,
    }];
    const state = makeState(playerDto(moss, actions), [fern, moss, ash]);

    render(
      <PlayerProvider players={[fern, moss, ash]}>
        <CampfireRing
          state={state}
          onAccept={jest.fn()}
          onDeny={jest.fn()}
          onOfferSeat={jest.fn()}
          onRequestSeat={requestSeat}
          onStartFire={startFire}
        />
      </PlayerProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Leave Fern's fire and start your own fire for 1 wood" }));
    fireEvent.click(screen.getByRole("button", { name: "Request seat at Ash's fire" }));

    expect(screen.getByText((_, element) => (
      element?.textContent === "Guest at Fern's fire. Guests may move to another fire or start their own."
    ))).toBeTruthy();
    expect(startFire).toHaveBeenCalledTimes(1);
    expect(requestSeat).toHaveBeenCalledWith(ash.id);
  });
});
