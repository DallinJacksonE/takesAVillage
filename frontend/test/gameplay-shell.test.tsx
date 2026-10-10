import { fireEvent, render, screen } from "@testing-library/react";
import GameplayShell from "../src/components/gameplay/layout/GameplayShell";

describe("GameplayShell", () => {
  it("keeps the map mounted while phase actions and chat are toggled", () => {
    render(
      <GameplayShell
        actionPanel={<div>Work choices</div>}
        chatPanel={<div>Village chat</div>}
        map={<div>Village map</div>}
        statusBar={<div>Village status</div>}
      />,
    );

    expect(screen.getByText("Village map")).toBeTruthy();
    expect(screen.queryByText("Work choices")).toBeNull();
    expect(screen.queryByText("Village chat")).toBeNull();

    const actionToggle = screen.getByRole("button", { name: "Open phase actions" });
    fireEvent.click(actionToggle);
    expect(actionToggle.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByText("Work choices")).toBeTruthy();

    const chatToggle = screen.getByRole("button", { name: "Open village chat" });
    fireEvent.click(chatToggle);
    expect(chatToggle.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByText("Village chat")).toBeTruthy();
  });

  it("shows and clears a phase-action attention dot when collapsed content changes", () => {
    const { rerender } = render(
      <GameplayShell
        actionAttentionKey="work-ready"
        actionPanel={<div>Work choices</div>}
        chatPanel={<div>Village chat</div>}
        map={<div>Village map</div>}
        statusBar={<div>Village status</div>}
      />,
    );

    expect(screen.queryByLabelText("Phase actions have updates")).toBeNull();

    rerender(
      <GameplayShell
        actionAttentionKey="new-work-offer"
        actionPanel={<div>Work choices</div>}
        chatPanel={<div>Village chat</div>}
        map={<div>Village map</div>}
        statusBar={<div>Village status</div>}
      />,
    );

    expect(screen.getByLabelText("Phase actions have updates")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Open phase actions" }));

    expect(screen.queryByLabelText("Phase actions have updates")).toBeNull();
  });

  it("closes an open phase panel with Escape and returns focus to its toggle", () => {
    render(
      <GameplayShell
        actionPanel={<button type="button">Choose work</button>}
        chatPanel={<div>Village chat</div>}
        map={<div>Village map</div>}
        statusBar={<div>Village status</div>}
      />,
    );

    const actionToggle = screen.getByRole("button", { name: "Open phase actions" });
    fireEvent.click(actionToggle);

    const panelButton = screen.getByRole("button", { name: "Choose work" });
    panelButton.focus();
    fireEvent.keyDown(screen.getByLabelText("Phase actions"), { key: "Escape" });

    expect(screen.queryByText("Choose work")).toBeNull();
    expect(document.activeElement).toBe(actionToggle);
  });
});
