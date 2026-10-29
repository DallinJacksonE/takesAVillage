import { render, screen } from "@testing-library/react";
import AvailableWorkCard from "../src/components/gameplay/AvailableWorkCard";
import { GameStateProvider } from "../src/components/hooks/useGameState";
import { PlayerProvider } from "../src/components/hooks/usePlayerName";
import type { DevelopmentDTO, GameStateDTO, PublicPlayerDTO, WorkActionDTO } from "../src/dtos";

const development: DevelopmentDTO = {
  id: "mine-1",
  type: "Mine",
  level: 3,
  maintenance_days: 2,
  owner_id: "player-1",
  maintenance_cost: {},
  upgrade_cost: {},
  can_upgrade: true,
  pending_contest: false,
};

const work: WorkActionDTO = {
  action_id: "contract-1",
  development,
  employer_id: "player-1",
  wage: 2,
  wage_type: "food",
};

const player: PublicPlayerDTO = {
  id: "player-1",
  name: "Moss",
  health: "healthy",
  fire_status: "COLD",
  fire_guests: [],
  developments: ["mine-1"],
  finished_phase: false,
  phase_state: "ACTIVE",
  visual_state: { animation: "IDLE", location: { kind: "HOME" } },
};

const gameState: GameStateDTO = {
  status: "ACTIVE",
  state_revision: 1,
  is_host: true,
  host_connected: true,
  me: {
    ...player,
    sickness_chance: 0,
    resources: { food: 1, wood: 0, iron: 0 },
    available_work: [work],
    committed_action: null,
    actions: [],
    timeline: [],
  },
  day: 1,
  phase: "WORK",
  time_remaining: 60,
  player_list: [player],
  public_interactions: [],
  map: [],
  developments: [development],
  chat_messages: [],
  chats: [],
  development_costs: {},
  max_fire_seats: 3,
  campfire_cost: { food: 1, wood: 1, iron: 0 },
  cold_sickness_rate: 0.3,
  hunger_sickness_rate: 0.5,
  recovery_rate: 0.2,
  training: false,
};

describe("AvailableWorkCard", () => {
  it("shows the development and agreed wage inline with each commit button", () => {
    render(
      <PlayerProvider players={[player]}>
        <GameStateProvider gameState={gameState}>
          <AvailableWorkCard
            onAcceptOffer={jest.fn()}
            onCommitWork={jest.fn()}
            onDenyOffer={jest.fn()}
          />
        </GameStateProvider>
      </PlayerProvider>,
    );

    const commitButton = screen.getByRole("button", {
      name: "Commit work at Mine mine-1 for agreed wage 2 food",
    });

    expect(commitButton.hasAttribute("disabled")).toBe(false);
    expect(screen.getByText("Mine mine-1")).toBeTruthy();
    expect(screen.getByText("Agreed wage: 2 food")).toBeTruthy();
  });
});
