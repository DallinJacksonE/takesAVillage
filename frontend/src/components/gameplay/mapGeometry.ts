import type { MapTileDTO, PlayerVisualLocation } from "../../dtos";

export interface MapPoint {
  x: number;
  y: number;
}

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

export const getPlayerMapPosition = (
  location: PlayerVisualLocation,
  mapData: MapTileDTO[],
  playerIndex: number,
  hexSize = 38,
): MapPoint => {
  if (location.kind === "FIRE") {
    if (location.slot === 0) return { x: 0, y: 26 };
    const guestIndex = location.slot - 1;
    const angle = guestIndex * (Math.PI / 2);
    return {
      x: Math.round(Math.cos(angle) * 58),
      y: 26 + Math.round(Math.sin(angle) * 40),
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
    const tile = Object.values(mapData).find(
      (candidate) => candidate.development?.id === location.id,
    );
    if (tile) {
      const point = axialToIsometric(tile.q, tile.r, hexSize);
      return { x: point.x, y: point.y - 36 };
    }
  }

  if (location.kind === "TILE") {
    const tile = Object.values(mapData).find(
      (candidate) => candidate.id === location.id,
    );
    if (tile) {
      const point = axialToIsometric(tile.q, tile.r, hexSize);
      return { x: point.x, y: point.y - 36 };
    }
  }

  return {
    x: (playerIndex % 5 - 2) * 38,
    y: 112 + Math.floor(playerIndex / 5) * 38,
  };
};
