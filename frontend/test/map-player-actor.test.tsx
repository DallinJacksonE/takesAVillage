import { act, fireEvent, render, screen } from "@testing-library/react";
import MapPlayerActor from "../src/components/gameplay/player/MapPlayerActor";
import type { PublicPlayerDTO } from "../src/dtos";

const player: PublicPlayerDTO = {
  id: "player-1",
  name: "Moss",
  health: "healthy",
  fire_status: "COLD",
  fire_guests: [],
  developments: [],
  finished_phase: true,
  phase_state: "INTENT_SUBMITTED",
  visual_state: {
    animation: "WORK_MINE",
    location: { kind: "DEVELOPMENT", id: "mine-1" },
  },
};

describe("MapPlayerActor", () => {
  it("walks into a changed location before playing the authoritative activity", () => {
    jest.useFakeTimers();
    render(<MapPlayerActor color="#fff" player={player} x={0} y={0} />);

    expect(screen.getByRole("img").getAttribute("aria-label")).toContain("walk");
    act(() => jest.advanceTimersByTime(600));
    expect(screen.getByRole("img").getAttribute("aria-label")).toContain("work mine");
    jest.useRealTimers();
  });

  it("faces trade partners toward each other while carrying", () => {
    const tradePlayer: PublicPlayerDTO = {
      ...player,
      visual_state: {
        animation: "CARRY",
        location: { kind: "TRADE", id: "trade-1", side: "TARGET" },
      },
    };
    render(<MapPlayerActor color="#fff" player={tradePlayer} x={0} y={0} />);

    expect(screen.getByRole("img").style.getPropertyValue("--sprite-direction")).toBe("-1");
  });

  it("opens the local player's reaction menu on right click", () => {
    const onReact = jest.fn();
    render(
      <MapPlayerActor
        color="#fff"
        player={player}
        x={0}
        y={0}
        isLocal
        onReact={onReact}
      />,
    );

    fireEvent.contextMenu(screen.getByText("Moss").parentElement!);
    fireEvent.click(screen.getByRole("menuitem", { name: "React with thumbs up" }));

    expect(onReact).toHaveBeenCalledWith("👍");
  });

  it("shows a public reaction until its expiry", () => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date("2026-08-19T13:00:00Z"));
    const reactingPlayer: PublicPlayerDTO = {
      ...player,
      reaction: {
        emoji: "😂",
        expires_at: Date.now() / 1000 + 4,
      },
    };
    render(<MapPlayerActor color="#fff" player={reactingPlayer} x={0} y={0} />);

    expect(screen.getByText("😂")).toBeTruthy();
    act(() => jest.advanceTimersByTime(4100));
    expect(screen.queryByText("😂")).toBeNull();
    jest.useRealTimers();
  });
});
