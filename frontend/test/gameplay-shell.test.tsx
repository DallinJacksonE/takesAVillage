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
});
