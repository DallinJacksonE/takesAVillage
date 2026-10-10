import { getActiveChatView } from "../src/components/gameplay/communication/chatViewTypes";

const chats = [{
  id: "chat-1",
  name: "Night Watch",
  member_ids: ["player-1", "player-2", "player-3"],
  creator_id: "player-1",
}];

describe("getActiveChatView", () => {
  it("includes every group member for the active-chat eyebrow", () => {
    expect(getActiveChatView("chat-1", chats).memberIds).toEqual([
      "player-1",
      "player-2",
      "player-3",
    ]);
  });

  it("marks the village chat as containing all players", () => {
    expect(getActiveChatView("global", chats).memberIds).toBeNull();
  });
});
