import {
  axialToIsometric,
  getPlayerMapPosition,
  getTradeGroupOffset,
} from "../src/components/gameplay/mapGeometry";

describe("axialToIsometric", () => {
  it("spaces pointy-top axial neighbours so their edges interlock", () => {
    expect(axialToIsometric(0, 0, 38)).toEqual({ x: 0, y: 0 });
    expect(axialToIsometric(1, 0, 38)).toEqual({
      x: expect.closeTo(65.8179, 3),
      y: 0,
    });
    expect(axialToIsometric(0, 1, 38)).toEqual({
      x: expect.closeTo(32.909, 3),
      y: 57,
    });
  });

  it("places workers at their authoritative development", () => {
    expect(getPlayerMapPosition(
      { kind: "DEVELOPMENT", id: "mine-1" },
      [{ id: "tile-1", q: 1, r: 0, type: "Mine", development: { id: "mine-1" } } as never],
      0,
    )).toEqual({
      x: expect.closeTo(65.8179, 3),
      y: -36,
    });
  });

  it("places accepted trade partners on opposite sides of a shared meeting point", () => {
    expect(getPlayerMapPosition(
      { kind: "TRADE", id: "trade-1", side: "INITIATOR" },
      [],
      0,
    )).toEqual({ x: -54, y: 12 });
    expect(getPlayerMapPosition(
      { kind: "TRADE", id: "trade-1", side: "TARGET" },
      [],
      1,
    )).toEqual({ x: 54, y: 12 });
  });

  it("separates simultaneous trades into deterministic clearing lanes", () => {
    const tradeIds = ["trade-b", "trade-a", "trade-b", "trade-c"];

    expect(getTradeGroupOffset("trade-a", tradeIds)).toEqual({ x: -140, y: 0 });
    expect(getTradeGroupOffset("trade-b", tradeIds)).toEqual({ x: 0, y: 0 });
    expect(getTradeGroupOffset("trade-c", tradeIds)).toEqual({ x: 140, y: 0 });
  });

  it("places fire groups around shared campfires and cold players apart", () => {
    expect(getPlayerMapPosition(
      { kind: "FIRE", id: "player-1", slot: 0 }, [], 0,
    )).toEqual({ x: 0, y: 26 });
    expect(getPlayerMapPosition(
      { kind: "FIRE", id: "player-1", slot: 1 }, [], 1,
    )).toEqual({ x: 58, y: 26 });
    expect(getPlayerMapPosition(
      { kind: "NIGHT_COLD", slot: 0 }, [], 2,
    )).toEqual({ x: -190, y: 96 });
  });
});
