import { fireEvent, render, screen } from "@testing-library/react";
import PlayerInfo from "../src/components/gameplay/playerInfo/PlayerInfo";
import PlayerRoster from "../src/components/gameplay/playerInfo/PlayerRoster";
import PlayerStatusCard from "../src/components/gameplay/playerInfo/PlayerStatusCard";
import { GameStateProvider } from "../src/components/hooks/useGameState";
import { PlayerColorProvider } from "../src/components/hooks/usePlayerColor";
import { PlayerProvider } from "../src/components/hooks/usePlayerName";
import type { GameStateDTO, PublicPlayerDTO } from "../src/dtos";

const mockPlayers: PublicPlayerDTO[] = [
  {
    id: "player-1",
    name: "Moss",
    health: "healthy",
    fire_status: "HOST",
    fire_guests: [],
    developments: ["dev-1"],
    finished_phase: false,
    phase_state: "ACTIVE",
    visual_state: { animation: "IDLE", location: { kind: "HOME" } },
  },
  {
    id: "player-2",
    name: "Fern",
    health: "sick",
    fire_status: "COLD",
    fire_guests: [],
    developments: [],
    finished_phase: false,
    phase_state: "ACTIVE",
    visual_state: { animation: "IDLE", location: { kind: "HOME" } },
  },
];

const mockGameState: GameStateDTO = {
  status: "ACTIVE",
  state_revision: 1,
  is_host: false,
  host_connected: true,
  day: 2,
  phase: "WORK",
  time_remaining: 45,
  player_list: mockPlayers,
  public_interactions: [],
  map: [],
  developments: [
    {
      id: "dev-1",
      type: "Farm",
      level: 2,
      maintenance_days: 3,
      owner_id: "player-1",
      maintenance_cost: { wood: 1 },
      upgrade_cost: { wood: 2 },
      can_upgrade: true,
      pending_contest: false,
      is_contested: false,
    },
  ],
  chat_messages: [],
  chats: [],
  development_costs: {},
  max_fire_seats: 3,
  campfire_cost: { food: 0, iron: 0, wood: 1 },
  cold_sickness_rate: 0.25,
  hunger_sickness_rate: 0.35,
  recovery_rate: 0.2,
  training: false,
  me: {
    id: "player-1",
    name: "Moss",
    health: "healthy",
    sickness_chance: 0.15,
    fire_status: "HOST",
    fire_guests: [],
    resources: { food: 3, iron: 1, wood: 4 },
    developments: ["dev-1"],
    available_work: [],
    committed_action: null,
    actions: [],
    timeline: [],
    finished_phase: false,
    phase_state: "ACTIVE",
  },
};

const renderWithProviders = (
  ui: React.ReactElement,
  gameState: GameStateDTO = mockGameState,
  players: PublicPlayerDTO[] = mockPlayers,
) => {
  return render(
    <GameStateProvider gameState={gameState}>
      <PlayerColorProvider gameState={gameState}>
        <PlayerProvider players={players}>{ui}</PlayerProvider>
      </PlayerColorProvider>
    </GameStateProvider>,
  );
};

describe("playerInfo components", () => {
  describe("PlayerInfo", () => {
    it("renders unknown player fallback when id does not match", () => {
      renderWithProviders(<PlayerInfo playerId="nonexistent" />);
      expect(screen.getByText("Unknown Player")).toBeTruthy();
    });

    it("renders player name and toggles tooltip on click and mouse enter/leave", () => {
      renderWithProviders(<PlayerInfo playerId="player-1" />);

      const trigger = screen.getByRole("button");
      expect(trigger.textContent).toContain("Moss");
      expect(trigger.textContent).toContain("😎");

      // Open on hover
      fireEvent.mouseEnter(trigger);
      expect(screen.getByRole("tooltip")).toBeTruthy();
      expect(screen.getByText("Farm (Lvl 2)")).toBeTruthy();

      // Close on leave
      fireEvent.mouseLeave(trigger);
      expect(screen.queryByRole("tooltip")).toBeNull();

      // Toggle on click
      fireEvent.click(trigger);
      expect(screen.getByRole("tooltip")).toBeTruthy();
    });

    it("closes tooltip when clicking outside", () => {
      renderWithProviders(
        <div>
          <button type="button">Outside Element</button>
          <PlayerInfo playerId="player-1" />
        </div>,
      );

      const trigger = screen.getByRole("button", { name: /Moss/ });
      fireEvent.click(trigger);
      expect(screen.getByRole("tooltip")).toBeTruthy();

      fireEvent.mouseDown(screen.getByRole("button", { name: "Outside Element" }));
      expect(screen.queryByRole("tooltip")).toBeNull();
    });
  });

  describe("PlayerRoster", () => {
    it("renders empty state when no players are available", () => {
      renderWithProviders(<PlayerRoster />, mockGameState, []);
      expect(screen.getByText("No Players Found.")).toBeTruthy();
    });

    it("renders roster with title and each player", () => {
      renderWithProviders(<PlayerRoster />);
      expect(screen.getByText("Village Roster")).toBeTruthy();
      expect(screen.getByText(/Moss/)).toBeTruthy();
      expect(screen.getByText(/Fern/)).toBeTruthy();
    });
  });

  describe("PlayerStatusCard", () => {
    it("renders current player resources and health statistics", () => {
      renderWithProviders(<PlayerStatusCard />);

      expect(screen.getByText("My Resources")).toBeTruthy();
      expect(screen.getByText("4")).toBeTruthy(); // wood
      expect(screen.getByText("3")).toBeTruthy(); // food
      expect(screen.getByText("1")).toBeTruthy(); // iron

      expect(screen.getByText("HEALTHY")).toBeTruthy();
      expect(screen.getByText("Sickness Chance: 15%")).toBeTruthy();
    });
  });
});
