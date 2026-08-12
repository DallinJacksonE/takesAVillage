import { describe, expect, it } from "vitest";

import type { OutboundGameEvent } from "@takes-a-village/shared";

import { deliverChatEvent, processGameEvent, type GameEventMessenger } from "../../../src/api/websocket/game-events.js";
import { Game } from "../../../src/game/game.js";

class RecordingMessenger implements GameEventMessenger {
  readonly broadcasts: OutboundGameEvent[] = [];
  readonly personal: Array<{ userId: string; packet: OutboundGameEvent }> = [];
  readonly stateBroadcasts: string[] = [];

  broadcast(_gameId: string, packet: OutboundGameEvent): void {
    this.broadcasts.push(packet);
  }

  sendPersonal(_gameId: string, userId: string, packet: OutboundGameEvent): void {
    this.personal.push({ userId, packet });
  }

  broadcastStates(game: Game): void {
    this.stateBroadcasts.push(game.id);
  }
}

describe("WebSocket game event routing", () => {
  it("delivers group chat only to group members", () => {
    const game = new Game("game-1", "player-1", "default", 0, false, () => 100);
    game.addPlayer("player-1");
    game.addPlayer("player-2");
    game.addPlayer("player-3");
    expect(game.createChat("player-1", "private", ["player-1", "player-2"])).toBe(true);
    const messenger = new RecordingMessenger();

    expect(deliverChatEvent(
      game,
      "player-1",
      { content: "secret", to_id: game.chats[0]!.id },
      messenger,
    )).toBe(true);

    expect(messenger.broadcasts).toEqual([]);
    expect(messenger.personal.map(({ userId }) => userId).sort()).toEqual(["player-1", "player-2"]);
    expect(messenger.personal.every(({ packet }) => packet.event === "new_chat_message")).toBe(true);
  });

  it("routes start, update, action, and chat-creation events with legacy recipient scope", () => {
    const game = new Game("game-1", "player-1", "default", 0, false, () => 100);
    game.addPlayer("player-1");
    game.addPlayer("player-2");
    const messenger = new RecordingMessenger();

    processGameEvent(game, "player-1", {
      event: "start_game_request",
      data: { gameId: game.id, userId: "player-1" },
    }, messenger);
    expect(messenger.broadcasts).toContainEqual({ event: "game_started", data: { day: 1 } });
    expect(messenger.stateBroadcasts).toEqual([game.id]);

    processGameEvent(game, "player-2", {
      event: "request_update",
      data: { gameId: game.id, userId: "player-2" },
    }, messenger);
    expect(messenger.personal.at(-1)).toMatchObject({
      userId: "player-2",
      packet: { event: "game_state" },
    });

    processGameEvent(game, "player-2", {
      event: "submit_action",
      data: { gameId: game.id, userId: "player-2", action_command: "INVALID", payload: {} },
    }, messenger);
    expect(messenger.personal.at(-1)).toEqual({
      userId: "player-2",
      packet: {
        event: "error",
        data: { message: "Action rejected by game rules.", action_command: "INVALID" },
      },
    });

    processGameEvent(game, "player-1", {
      event: "create_chat",
      data: { gameId: game.id, userId: "player-1", name: "team", memberIds: ["player-2"] },
    }, messenger);
    expect(game.chats).toHaveLength(1);
    expect(messenger.stateBroadcasts).toEqual([game.id, game.id]);
  });
});
