import { render, screen } from "@testing-library/react";
import VillageMap from "../src/components/gameplay/VillageMap";
import { PlayerProvider } from "../src/components/hooks/usePlayerName";
import type { PublicPlayerDTO } from "../src/dtos";

const makePlayer = (
  id: string,
  location: PublicPlayerDTO["visual_state"]["location"],
): PublicPlayerDTO => ({
  id,
  name: id === "player-1" ? "Moss" : "Fern",
  health: "healthy",
  fire_status: id === "player-1" ? "HOST" : "GUEST",
  fire_guests: id === "player-1" ? ["player-2"] : [],
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
        />
      </PlayerProvider>,
    );

    expect(screen.getByLabelText("Night clearing")).toBeTruthy();
    expect(screen.getByLabelText("Campfire hosted by Moss")).toBeTruthy();
  });
});