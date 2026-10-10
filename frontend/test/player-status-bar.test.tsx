import { render, screen } from "@testing-library/react";
import PlayerStatusBar from "../src/components/gameplay/layout/PlayerStatusBar";

describe("PlayerStatusBar", () => {
  it("keeps player identity, round context, and timer visible", () => {
    render(
      <PlayerStatusBar
        day={3}
        phase="WORK"
        playerName="Moss"
        sprite={<span aria-label="Moss goblin" />}
        timeLeft={30}
      />,
    );

    expect(screen.getByText("Moss")).toBeTruthy();
    expect(screen.getByLabelText("Moss goblin")).toBeTruthy();
    expect(screen.getByText("Day 3 · WORK")).toBeTruthy();
    expect(screen.getByRole("timer").textContent).toContain("30");
    expect(screen.getByRole("timer").getAttribute("data-severity")).toBe("warning");
  });
});
