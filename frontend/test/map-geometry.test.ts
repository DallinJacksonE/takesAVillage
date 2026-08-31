import {
  axialToIsometric,
  getHexSlotForOccupantIndex,
  getHexSlotPosition,
  getNightFireAnchor,
  getPlayerMapPosition,
  getTradeGroupOffset,
  HEX_SLOT_SPREAD_ORDER,
  TOTAL_HEX_SLOTS,
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
});

describe("getHexSlotPosition", () => {
  it("has exactly 10 slots configured", () => {
    expect(TOTAL_HEX_SLOTS).toBe(10);
  });

  it("places slot 0 at the tightened building position in the same orientation", () => {
    const center = { x: 100, y: 100 };
    const hexSize = 38;
    const slot0 = getHexSlotPosition(center, 0, hexSize);

    // baseDx = -19 * 0.75 = -14.25 -> -14
    // baseDy = 20 * 0.75 = 15
    expect(slot0).toEqual({
      x: 100 - 14,
      y: 100 + 15,
    });
  });

  it("generates 10 unique positions around the hex center with constant radius", () => {
    const center = { x: 0, y: 0 };
    const hexSize = 38;
    const positions = Array.from({ length: 10 }, (_, slot) =>
      getHexSlotPosition(center, slot, hexSize)
    );

    // Ensure all 10 positions are distinct
    const uniquePositions = new Set(
      positions.map((p) => `${p.x},${p.y}`)
    );
    expect(uniquePositions.size).toBe(10);

    // Verify constant radius from center for all positions (within integer rounding tolerance)
    const expectedRadius = Math.sqrt(Math.pow(-14.25, 2) + Math.pow(15, 2)); // ~20.69
    positions.forEach((pos) => {
      const dist = Math.sqrt(pos.x * pos.x + pos.y * pos.y);
      expect(Math.abs(dist - expectedRadius)).toBeLessThanOrEqual(1.5);
    });
  });

  it("wraps slot numbers modulo 10 correctly", () => {
    const center = { x: 50, y: 50 };
    expect(getHexSlotPosition(center, 10, 38)).toEqual(
      getHexSlotPosition(center, 0, 38)
    );
    expect(getHexSlotPosition(center, 13, 38)).toEqual(
      getHexSlotPosition(center, 3, 38)
    );
    expect(getHexSlotPosition(center, -1, 38)).toEqual(
      getHexSlotPosition(center, 9, 38)
    );
  });
});

describe("getHexSlotForOccupantIndex", () => {
  it("enters every other slot first (0, 2, 4, 6, 8) then fills remaining slots (1, 3, 5, 7, 9)", () => {
    expect(HEX_SLOT_SPREAD_ORDER).toEqual([0, 2, 4, 6, 8, 1, 3, 5, 7, 9]);

    const expectedOrder = [0, 2, 4, 6, 8, 1, 3, 5, 7, 9];
    expectedOrder.forEach((expectedSlot, occupantIndex) => {
      expect(getHexSlotForOccupantIndex(occupantIndex)).toBe(expectedSlot);
    });
  });

  it("handles wrapping for more than 10 occupants on the same hex", () => {
    expect(getHexSlotForOccupantIndex(10)).toBe(0);
    expect(getHexSlotForOccupantIndex(11)).toBe(2);
    expect(getHexSlotForOccupantIndex(15)).toBe(1);
  });
});

describe("getPlayerMapPosition", () => {
  it("places workers and builders at slot 0 on their hex by default", () => {
    const tileCenter = axialToIsometric(1, 0, 38);
    const expectedSlot0 = getHexSlotPosition(tileCenter, 0, 38);

    const devPos = getPlayerMapPosition(
      { kind: "DEVELOPMENT", id: "mine-1" },
      [{ id: "tile-1", q: 1, r: 0, type: "Mine", development: { id: "mine-1" } } as never],
      0,
      38,
    );
    expect(devPos).toEqual(expectedSlot0);

    const tilePos = getPlayerMapPosition(
      { kind: "TILE", id: "tile-1" },
      [{ id: "tile-1", q: 1, r: 0, type: "Mine" } as never],
      0,
      38,
    );
    expect(tilePos).toEqual(expectedSlot0);
  });

  it("places additional workers at subsequent hex slots 1..9", () => {
    const tileCenter = axialToIsometric(0, 0, 38);
    const mapData = [{ id: "tile-1", q: 0, r: 0, type: "Farm", development: { id: "farm-1" } } as never];

    for (let slot = 0; slot < 10; slot++) {
      const pos = getPlayerMapPosition(
        { kind: "DEVELOPMENT", id: "farm-1", slot },
        mapData,
        slot,
        38,
      );
      expect(pos).toEqual(getHexSlotPosition(tileCenter, slot, 38));
    }
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

  it("places the host and guests at night campfires while keeping cold placement unchanged", () => {
    const hostPos = getPlayerMapPosition(
      { kind: "FIRE", id: "player-1", slot: 0 }, [], 0, 38, [], 4,
    );
    expect(hostPos).toBeDefined();

    expect(getPlayerMapPosition(
      { kind: "NIGHT_COLD", slot: 0 }, [], 2,
    )).toEqual({ x: -190, y: 96 });
  });

  it("gives every host an independent fire and keeps each guest with that host", () => {
    const fireIds = ["fire-c", "fire-a", "fire-b"];

    const firstHost = getPlayerMapPosition(
      { kind: "FIRE", id: "fire-a", slot: 0 }, [], 0, 38, fireIds,
    );
    const secondHost = getPlayerMapPosition(
      { kind: "FIRE", id: "fire-b", slot: 0 }, [], 1, 38, fireIds,
    );
    const guest = getPlayerMapPosition(
      { kind: "FIRE", id: "fire-a", slot: 1 }, [], 2, 38, fireIds, 3,
    );
    const anchor = getNightFireAnchor("fire-a", fireIds, 3);

    expect(firstHost).not.toEqual(secondHost);
    expect(firstHost.x).toBe(anchor.x);
    expect(guest).toEqual(getPlayerMapPosition(
      { kind: "FIRE", id: "fire-a", slot: 1 }, [], 2, 38, fireIds, 3,
    ));
  });
});

