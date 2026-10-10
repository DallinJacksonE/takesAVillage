import { fireEvent, render, screen } from "@testing-library/react";
import VillageMap from "../src/components/gameplay/VillageMap";
import { PlayerProvider } from "../src/components/hooks/usePlayerName";
import type { MapTileDTO, PublicPlayerDTO } from "../src/dtos";

jest.mock(
  "../src/components/gameplay/playerInfo/PlayerInfo",
  () => () => <span>Development owner</span>,
);

const players: PublicPlayerDTO[] = [
  {
    id: "player-1",
    name: "Moss",
    health: "healthy",
    fire_status: "COLD",
    fire_guests: [],
    developments: [],
    finished_phase: false,
    phase_state: "ACTIVE",
    visual_state: { animation: "IDLE", location: { kind: "HOME" } },
  },
  {
    id: "player-2",
    name: "Fern",
    health: "healthy",
    fire_status: "COLD",
    fire_guests: [],
    developments: ["farm-1"],
    finished_phase: false,
    phase_state: "ACTIVE",
    visual_state: { animation: "IDLE", location: { kind: "HOME" } },
  },
];

const mapData: MapTileDTO[] = [{
  id: "tile-1",
  q: 0,
  r: 0,
  type: "Farm",
  development: {
    id: "farm-1",
    type: "Farm",
    level: 1,
    maintenance_days: 3,
    owner_id: "player-2",
    is_contested: false,
    maintenance_cost: { wood: 1 },
    upgrade_cost: { wood: 2 },
    can_upgrade: true,
    pending_contest: false,
  },
}];

describe("VillageMap development actions", () => {
  it("initiates a contest when a player contests another player's stable development", () => {
    const onContest = jest.fn();
    const { container } = render(
      <PlayerProvider players={players}>
        <VillageMap
          mapData={mapData}
          onBuild={jest.fn()}
          onContest={onContest}
          playerId="player-1"
          development_costs={{}}
          players={players}
          phase="WORK"
        />
      </PlayerProvider>,
    );

    fireEvent.click(container.querySelector(".hexTile")!);
    fireEvent.click(screen.getByRole("button", { name: "Contest Property" }));

    expect(onContest).toHaveBeenCalledWith("farm-1", "INITIATOR");
  });
});
