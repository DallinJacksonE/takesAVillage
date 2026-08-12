import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import {
  botJoinRequestSchema,
  inboundGameEventSchema,
  spawnBotsRequestSchema,
  spawnBotsResponseSchema,
} from "../src/index.js";

interface BotWireFixture {
  spawnRequest: unknown;
  spawnResponse: unknown;
  botJoinRequest: unknown;
  outboundWebSocketPackets: unknown[];
}

function loadFixture(): BotWireFixture {
  return JSON.parse(readFileSync(resolve("fixtures/bot-wire.json"), "utf8")) as BotWireFixture;
}

describe("language-neutral bot wire fixtures", () => {
  it("matches every shared service-to-bot contract", () => {
    const fixture = loadFixture();

    expect(spawnBotsRequestSchema.parse(fixture.spawnRequest)).toEqual(fixture.spawnRequest);
    expect(spawnBotsResponseSchema.parse(fixture.spawnResponse)).toEqual(fixture.spawnResponse);
    expect(botJoinRequestSchema.parse(fixture.botJoinRequest)).toEqual(fixture.botJoinRequest);
    for (const packet of fixture.outboundWebSocketPackets) {
      expect(inboundGameEventSchema.parse(packet)).toEqual(packet);
    }
  });
});
