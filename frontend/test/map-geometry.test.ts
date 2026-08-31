import {
  axialToIsometric,
  getHexSlotForOccupantIndex,
  getHexSlotPosition,
  getNightFireAnchor,
  getNightFireSeatPosition,
  getPlayerMapPosition,
  getTradeGroupOffset,
  HEX_SLOT_SPREAD_ORDER,
  TOTAL_HEX_SLOTS,
} from "../src/components/gameplay/mapGeometry";
import type { MapDataDTO } from "../src/dtos";

const MAX_FIRE_SEATS = 3;

const mapData: MapDataDTO = [{
  id: "tile-1",
  q: 1,
  r: 0,
  type: "Mine",
  development: {
    id: "mine-1",
    type: "Mine",
    level: 1,
    maintenance_days: 0,
    owner_id: "player-1",
    maintenance_cost: {},
    upgrade_cost: {},
    can_upgrade: false,
    pending_contest: false,
  },
}];

describe("axialToIsometric", () => {
  it("spaces pointy-top axial neighbours so their edges interlock", () => {
    expect(axialToIsometric(0, 0, 38)).toEqual({ x: 0, y: 0 });
    expect(axialToIsometric(1, 0, 38).x).toBeCloseTo(65.8179, 3);
    expect(axialToIsometric(1, 0, 38).y).toBe(0);
    expect(axialToIsometric(0, 1, 38).x).toBeCloseTo(32.909, 3);
    expect(axialToIsometric(0, 1, 38).y).toBe(57);
  });
});

describe("getPlayerMapPosition", () => {
  it("places workers at their authoritative development", () => {
    const position = getPlayerMapPosition(
      { kind: "DEVELOPMENT", id: "mine-1" },
      mapData,
      0,
      38,
      [],
      MAX_FIRE_SEATS,
    );

    expect(position.x).toBeCloseTo(65.8179, 3);
    expect(position.y).toBe(0);
  });

  it("places accepted trade partners on opposite sides of a shared meeting point", () => {
    expect(getPlayerMapPosition(
      { kind: "TRADE", id: "trade-1", side: "INITIATOR" },
      [],
      0,
      38,
      [],
      MAX_FIRE_SEATS,
    )).toEqual({ x: -54, y: 12 });
    expect(getPlayerMapPosition(
      { kind: "TRADE", id: "trade-1", side: "TARGET" },
      [],
      1,
      38,
      [],
      MAX_FIRE_SEATS,
    )).toEqual({ x: 54, y: 12 });
  });

  it("places players without a mapped location in deterministic rows", () => {
    expect(getPlayerMapPosition(
      { kind: "HOME" }, [], 6, 38, [], MAX_FIRE_SEATS,
    )).toEqual({ x: -38, y: 150 });
  });

  it("places cold players in a four-column grid", () => {
    expect(getPlayerMapPosition(
      { kind: "NIGHT_COLD", slot: 5 }, [], 2, 38, [], MAX_FIRE_SEATS,
    )).toEqual({ x: -64, y: 154 });
  });
});

describe("getTradeGroupOffset", () => {
  it("separates unique trades into sorted clearing lanes", () => {
    const tradeIds = ["trade-b", "trade-a", "trade-b", "trade-c"];

    expect(getTradeGroupOffset("trade-a", tradeIds)).toEqual({ x: -140, y: 0 });
    expect(getTradeGroupOffset("trade-b", tradeIds)).toEqual({ x: 0, y: 0 });
    expect(getTradeGroupOffset("trade-c", tradeIds)).toEqual({ x: 140, y: 0 });
  });
});

describe("night fire geometry", () => {
  it("places a host and three guests on a regular polygon around one fire", () => {
    const seats = [0, 1, 2, 3].map((slot) =>
      getNightFireSeatPosition("fire-a", slot, MAX_FIRE_SEATS, ["fire-a"]));

    expect(seats).toEqual([
      { x: 0, y: -107 },
      { x: 107, y: 0 },
      { x: 0, y: 107 },
      { x: -107, y: 0 },
    ]);
  });

  it("assigns each fire a stable anchor after sorting and deduplicating ids", () => {
    const fireIds = ["fire-c", "fire-a", "fire-b", "fire-a"];

    expect(getNightFireAnchor("fire-a", fireIds, 4)).toEqual({ x: 0, y: -193 });
    expect(getNightFireAnchor("fire-b", fireIds, 4)).toEqual({ x: 167, y: 96 });
    expect(getNightFireAnchor("fire-c", fireIds, 4)).toEqual({ x: -167, y: 96 });
  });

  it("keeps every player at the polygon for their own fire", () => {
    const fireIds = ["fire-a", "fire-b"];
    const anchor = getNightFireAnchor("fire-b", fireIds, 4);

    expect(getPlayerMapPosition(
      { kind: "FIRE", id: "fire-b", slot: 0 },
      [],
      0,
      38,
      fireIds,
      MAX_FIRE_SEATS,
    )).toEqual({ x: anchor.x, y: anchor.y - 107 });

    expect(getPlayerMapPosition(
      { kind: "FIRE", id: "fire-b", slot: 1 },
      [],
      1,
      38,
      fireIds,
      MAX_FIRE_SEATS,
    )).toEqual({ x: anchor.x + 107, y: anchor.y });
  });
});
