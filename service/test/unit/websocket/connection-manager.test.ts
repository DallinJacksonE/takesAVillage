import { describe, expect, it } from "vitest";

import { ConnectionManager, type SocketConnection } from "../../../src/api/websocket/connection-manager.js";

class Socket implements SocketConnection {
  closeCode: number | undefined;
  readonly sent: string[] = [];

  constructor(private readonly fails = false) {}

  send(data: string): void {
    if (this.fails) throw new Error("closed");
    this.sent.push(data);
  }

  close(code?: number): void {
    this.closeCode = code;
  }
}

class AsyncFailureSocket implements SocketConnection {
  send(_data: string, callback?: (error?: Error) => void): void {
    callback?.(new Error("asynchronous failure"));
  }

  close(): void {}
}

describe("WebSocket connection manager", () => {
  it("keeps a replacement connection when the old socket disconnects", () => {
    const manager = new ConnectionManager();
    const oldSocket = new Socket();
    const replacement = new Socket();

    manager.connect(oldSocket, "game-1", "player-1");
    manager.connect(replacement, "game-1", "player-1");

    expect(oldSocket.closeCode).toBe(4001);
    expect(manager.disconnect(oldSocket, "game-1", "player-1")).toBe(false);
    expect(manager.get("game-1", "player-1")).toBe(replacement);
  });

  it("removes a failed broadcast recipient without blocking healthy sockets", () => {
    const failedRecipients: Array<[string, string]> = [];
    const manager = new ConnectionManager((gameId, userId) => failedRecipients.push([gameId, userId]));
    const healthy = new Socket();
    const failed = new Socket(true);
    manager.connect(healthy, "game-1", "healthy");
    manager.connect(failed, "game-1", "failed");

    manager.broadcast("game-1", { event: "room_update", data: { player_count: 2 } });

    expect(healthy.sent).toEqual([
      JSON.stringify({ event: "room_update", data: { player_count: 2 } }),
    ]);
    expect(manager.get("game-1", "failed")).toBeUndefined();
    expect(failedRecipients).toEqual([["game-1", "failed"]]);
  });

  it("removes a recipient after an asynchronous transport failure", () => {
    const failures: string[] = [];
    const manager = new ConnectionManager((_gameId, userId) => failures.push(userId));
    manager.connect(new AsyncFailureSocket(), "game-1", "failed");

    manager.broadcast("game-1", { event: "room_update", data: { player_count: 1 } });

    expect(manager.get("game-1", "failed")).toBeUndefined();
    expect(failures).toEqual(["failed"]);
  });
});
