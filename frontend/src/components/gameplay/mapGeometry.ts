import type { MapDataDTO, PlayerVisualLocation } from "../../dtos";

export interface MapPoint {
  x: number;
  y: number;
}

const FIRE_GROUP_RADIUS = 150;
const FIRE_GUEST_RADIUS_X = 58;
const FIRE_GUEST_RADIUS_Y = 40;
const FIRE_CENTER_Y = 26;

export const axialToIsometric = (q: number, r: number, hexSize: number): MapPoint => ({
  x: hexSize * Math.sqrt(3) * (q + r / 2),
  y: hexSize * 1.5 * r,
});

export const getTradeGroupOffset = (
  tradeId: string,
  tradeIds: string[],
): MapPoint => {
  const uniqueTradeIds = [...new Set(tradeIds)].sort();
  const tradeIndex = uniqueTradeIds.indexOf(tradeId);
  return {
    x: (tradeIndex - (uniqueTradeIds.length - 1) / 2) * 140,
    y: 0,
  };
};

const mapTiles = (mapData: MapDataDTO) => (
  Array.isArray(mapData) ? mapData : Object.values(mapData)
);

export const getNightFireAnchor = (fireId: string, fireIds: string[]): MapPoint => {
  const uniqueFireIds = [...new Set(fireIds)].sort();
  const fireIndex = uniqueFireIds.indexOf(fireId);
  if (fireIndex < 0 || uniqueFireIds.length <= 1) {
    return { x: 0, y: FIRE_CENTER_Y };
  }

  const angle = -Math.PI / 2 + (fireIndex * 2 * Math.PI) / uniqueFireIds.length;
  return {
    x: Math.round(Math.cos(angle) * FIRE_GROUP_RADIUS),
    y: FIRE_CENTER_Y + Math.round(Math.sin(angle) * FIRE_GROUP_RADIUS),
  };
};

export const getPlayerMapPosition = (
  location: PlayerVisualLocation,
  mapData: MapDataDTO,
  playerIndex: number,
  hexSize = 38,
  fireIds: string[] = [],
): MapPoint => {
  if (location.kind === "FIRE") {
    const anchor = getNightFireAnchor(location.id, fireIds);
    if (location.slot === 0) return anchor;
    const guestIndex = location.slot - 1;
    const angle = guestIndex * (Math.PI / 2);
    return {
      x: anchor.x + Math.round(Math.cos(angle) * FIRE_GUEST_RADIUS_X),
      y: anchor.y + Math.round(Math.sin(angle) * FIRE_GUEST_RADIUS_Y),
    };
  }

  if (location.kind === "NIGHT_COLD") {
    return {
      x: -190 + (location.slot % 4) * 126,
      y: 96 + Math.floor(location.slot / 4) * 58,
    };
  }

  if (location.kind === "TRADE") {
    return {
      x: location.side === "INITIATOR" ? -54 : 54,
      y: 12,
    };
  }

  if (location.kind === "DEVELOPMENT") {
    const tile = mapTiles(mapData).find(
      (candidate) => candidate.development?.id === location.id,
    );
    if (tile) {
      const point = axialToIsometric(tile.q, tile.r, hexSize);
      return { x: point.x, y: point.y };
    }
  }

  if (location.kind === "TILE") {
    const tile = mapTiles(mapData).find(
      (candidate) => candidate.id === location.id,
    );
    if (tile) {
      const point = axialToIsometric(tile.q, tile.r, hexSize);
      return { x: point.x, y: point.y };
    }
  }

  return {
    x: (playerIndex % 5 - 2) * 38,
    y: 112 + Math.floor(playerIndex / 5) * 38,
  };
};
