import { render, screen } from "@testing-library/react";
import VillageMap from "../src/components/gameplay/VillageMap";
import { PlayerProvider } from "../src/components/hooks/usePlayerName";
import type { PublicPlayerDTO } from "../src/dtos";

const makePlayer = (
  id: string,
  location: PublicPlayerDTO["visual_state"]["location"],
): PublicPlayerDTO => ({
  id,
  name: id === "player-1" ? "Moss" : id === "player-3" ? "Ash" : "Fern",
  health: "healthy",
  fire_status: location.kind === "FIRE" && location.slot === 0 ? "HOST" : "GUEST",
  fire_guests: id === "player-1" ? ["player-2"] : id === "player-3" ? ["player-4"] : [],
  developments: [],
  finished_phase: false,
  phase_state: "ACTIVE",
  visual_state: { animation: "IDLE", location },
});

describe("NIGHT village scene", () => {
  it("renders one campfire prop for a host and keeps the axial map hidden", () => {
    const players = [
      makePlayer("player-1", { kind: "FIRE", id: "player-1", slot: 0 }),
      makePlayer("player-2", { kind: "FIRE", id: "player-1", slot: 1 }),
    ];
    render(
      <PlayerProvider players={players}>
        <VillageMap
          mapData={[]}
          onBuild={jest.fn()}
          playerId="player-1"
          development_costs={{}}
          players={players}
          phase="NIGHT"
          maxFireSeats={4}
        />
      </PlayerProvider>,
    );

    expect(screen.getByLabelText("Night clearing")).toBeTruthy();
    expect(screen.getByLabelText("Campfire hosted by Moss")).toBeTruthy();
  });

  it("renders multiple host campfires at separate clearing points", () => {
    const players = [
      makePlayer("player-1", { kind: "FIRE", id: "player-1", slot: 0 }),
      makePlayer("player-2", { kind: "FIRE", id: "player-1", slot: 1 }),
      makePlayer("player-3", { kind: "FIRE", id: "player-3", slot: 0 }),
      makePlayer("player-4", { kind: "FIRE", id: "player-3", slot: 1 }),
    ];
    render(
      <PlayerProvider players={players}>
        <VillageMap
          mapData={[]}
          onBuild={jest.fn()}
          playerId="player-1"
          development_costs={{}}
          players={players}
          phase="NIGHT"
          maxFireSeats={4}
        />
      </PlayerProvider>,
    );

    const mossFire = screen.getByLabelText("Campfire hosted by Moss");
    const ashFire = screen.getByLabelText("Campfire hosted by Ash");

    expect(mossFire).toBeTruthy();
    expect(ashFire).toBeTruthy();
    expect(mossFire.getAttribute("style")).not.toEqual(ashFire.getAttribute("style"));

    expect(screen.getAllByLabelText(/Available fire seat|Available host seat/)).toHaveLength(4);
  });

  it("renders only unoccupied seat markers for each host fire", () => {
    const players = [
      makePlayer("player-1", { kind: "FIRE", id: "player-1", slot: 0 }),
      makePlayer("player-2", { kind: "FIRE", id: "player-1", slot: 1 }),
      makePlayer("player-3", { kind: "FIRE", id: "player-3", slot: 0 }),
    ];
    render(
      <PlayerProvider players={players}>
        <VillageMap
          mapData={[]}
          onBuild={jest.fn()}
          playerId="player-1"
          development_costs={{}}
          players={players}
          phase="NIGHT"
          maxFireSeats={3}
        />
      </PlayerProvider>,
    );

    expect(screen.getAllByLabelText(/Available fire seat|Available host seat/)).toHaveLength(3);
  });
});
