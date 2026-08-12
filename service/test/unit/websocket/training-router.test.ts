import { describe, expect, it } from "vitest";

import {
  TrainingUpdateHub,
  type TrainingSocket,
} from "../../../src/api/websocket/training-router.js";

class Socket implements TrainingSocket {
  readonly packets: unknown[] = [];

  constructor(private readonly fails = false) {}

  send(data: string): void {
    if (this.fails) throw new Error("disconnected");
    this.packets.push(JSON.parse(data));
  }
}

describe("training WebSocket updates", () => {
  it("sends current state and broadcasts updates while removing failed sockets", () => {
    const hub = new TrainingUpdateHub();
    const good = new Socket();
    const failed = new Socket(true);
    hub.connect(good);
    hub.connect(failed);
    hub.sendCurrent(good, { sessions: [] });
    hub.broadcast({
      sessions: [{
        session_id: "session-1",
        ruleset: "default",
        bot_count: 2,
        generation: 1,
        generations_left: 1,
        population_size: 2,
        generation_statistics: [],
      }],
    });

    expect(good.packets).toEqual([
      { event: "training_sessions", data: { sessions: [] } },
      { event: "training_sessions", data: { sessions: [expect.objectContaining({ session_id: "session-1" })] } },
    ]);
    expect(hub.size).toBe(1);
  });
});
