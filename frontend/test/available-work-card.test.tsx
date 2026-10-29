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
  wage: 3,
  wage_type: "iron",
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
  it.each([
    { type: "Farm" as const, resource: "food" as const },
    { type: "Woods" as const, resource: "wood" as const },
    { type: "Mine" as const, resource: "iron" as const },
  ])("shows an owned $type as My with its default wage", ({ type, resource }) => {
    const ownedDevelopment = { ...development, type, level: 3 };
    const ownedWork = { ...work, development: ownedDevelopment, wage: 3, wage_type: resource };
    const state = {
      ...gameState,
      me: { ...gameState.me, available_work: [ownedWork] },
    };

    render(
      <PlayerProvider players={[player]}>
        <GameStateProvider gameState={state}>
          <AvailableWorkCard
            onAcceptOffer={jest.fn()}
            onCommitWork={jest.fn()}
            onDenyOffer={jest.fn()}
          />
        </GameStateProvider>
      </PlayerProvider>,
    );

    const wageLabel = `3 ${resource}`;
    const commitButton = screen.getByRole("button", {
      name: `Commit work at My ${type} for default wage ${wageLabel}`,
    });

    expect(commitButton.hasAttribute("disabled")).toBe(false);
    expect(screen.getByText(`My ${type}`)).toBeTruthy();
    expect(screen.getByText(`Default wage: ${wageLabel}`)).toBeTruthy();
  });

  it("shows another player's development with their possessive name", () => {
    const otherPlayer = { ...player, id: "player-2", name: "Fern" };
    const otherDevelopment = { ...development, owner_id: otherPlayer.id };
    const otherWork = {
      ...work,
      development: otherDevelopment,
      employer_id: otherPlayer.id,
      wage: 2,
      wage_type: "wood" as const,
    };
    const state = {
      ...gameState,
      me: { ...gameState.me, available_work: [otherWork] },
    };

    render(
      <PlayerProvider players={[player, otherPlayer]}>
        <GameStateProvider gameState={state}>
          <AvailableWorkCard
            onAcceptOffer={jest.fn()}
            onCommitWork={jest.fn()}
            onDenyOffer={jest.fn()}
          />
        </GameStateProvider>
      </PlayerProvider>,
    );

    expect(screen.getByText("Fern's Mine")).toBeTruthy();
    expect(screen.getByText("Agreed wage: 2 wood")).toBeTruthy();
    expect(
      screen.getByRole("button", {
        name: "Commit work at Fern's Mine for agreed wage 2 wood",
      }),
    ).toBeTruthy();
  });
});
