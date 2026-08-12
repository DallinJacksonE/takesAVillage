import { afterEach, describe, expect, it, vi } from "vitest";

import { ConnectionManager, type SocketConnection } from "../../../src/api/websocket/connection-manager.js";
import { cleanupDisconnectedPlayer } from "../../../src/api/websocket/game-router.js";
import { Game } from "../../../src/game/game.js";

class Socket implements SocketConnection {
  readonly packets: unknown[] = [];

  send(data: string): void {
    this.packets.push(JSON.parse(data));
  }

  close(): void {}
}

afterEach(() => vi.unstubAllGlobals());

describe("game WebSocket disconnect cleanup", () => {
  it("removes and respawns a disconnected waiting-game bot", () => {
    const fetch = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetch);
    const game = new Game("game-1", "host", "default", 1, false, () => 100);
    game.addPlayer("host");
    game.addPlayer("bot_1234");
    const games = new Map([[game.id, game]]);
    const connections = new ConnectionManager();
    const hostSocket = new Socket();
    connections.connect(hostSocket, game.id, "host");

    cleanupDisconnectedPlayer(game.id, "bot_1234", {
      games,
      connections,
      botSecret: "test-secret",
      botServiceUrl: "http://bots:8001",
    });

    expect(game.players.has("bot_1234")).toBe(false);
    expect(hostSocket.packets).toContainEqual({ event: "room_update", data: { player_count: 1 } });
    expect(fetch).toHaveBeenCalledWith("http://bots:8001/api/spawn_bots", expect.objectContaining({
      method: "POST",
      body: expect.stringContaining('"botCount":1'),
    }));
  });
});
