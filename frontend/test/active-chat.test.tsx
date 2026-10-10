import { render, screen } from "@testing-library/react";
import ActiveChat from "../src/components/gameplay/communication/ActiveChat";

it("shows the active chat members above the message history", () => {
  render(
    <ActiveChat
      activeChat={{
        id: "chat-1",
        label: "#Night Watch",
        recipientId: "chat-1",
        showSenderNames: true,
        memberIds: ["player-1", "player-2"],
      }}
      getPlayerName={(id) => id === "player-1" ? "Moss" : "Fern"}
      inputValue=""
      messages={[]}
      onInputChange={() => undefined}
      onSend={() => undefined}
      playerId="player-1"
    />,
  );

  expect(screen.getByText("Members")).toBeTruthy();
  expect(screen.getByText("Moss · Fern")).toBeTruthy();
});
