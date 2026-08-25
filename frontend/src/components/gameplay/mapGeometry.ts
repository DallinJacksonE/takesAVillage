import type { MapDataDTO, PlayerVisualLocation } from "../../dtos";

export interface MapPoint {
  x: number;
  y: number;
}

const FIRE_CENTER_Y = 26;
const MIN_SEAT_CENTER_DISTANCE = 150;
const MIN_FIRE_GROUP_RADIUS = 64;
const MIN_FIRE_GROUP_PADDING = 120;

/**
 * Returns the circumradius of a regular polygon whose adjacent
 * vertices are at least MIN_SEAT_CENTER_DISTANCE apart.
 *
 * Chord length:
 *   d = 2R sin(pi / n)
 *
 * Therefore:
 *   R = d / (2 sin(pi / n))
 */
const getFirePolygonRadius = (vertexCount: number): number => {
  if (vertexCount <= 1) {
    return MIN_FIRE_GROUP_RADIUS;
  }

  const radius =
    MIN_SEAT_CENTER_DISTANCE /
    (2 * Math.sin(Math.PI / vertexCount));

  return Math.max(
    MIN_FIRE_GROUP_RADIUS,
    Math.ceil(radius),
  );
};

export const axialToIsometric = (
  q: number,
  r: number,
  hexSize: number,
): MapPoint => ({
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
  Array.isArray(mapData)
    ? mapData
    : Object.values(mapData)
);

/**
 * Returns the center position of a fire.
 *
 * Every fire is placed on the same large ring around the map center,
 * with enough separation for its polygon seating area.
 */
export const getNightFireAnchor = (
  fireId: string,
  fireIds: string[],
  maxFireSeats = 3,
): MapPoint => {
  const uniqueFireIds = [...new Set(fireIds)].sort();
  const fireIndex = uniqueFireIds.indexOf(fireId);

  if (fireIndex < 0 || uniqueFireIds.length <= 1) {
    return {
      x: 0,
      y: FIRE_CENTER_Y,
    };
  }

  // maxFireSeats is the TOTAL number of polygon vertices.
  const vertexCount = Math.max(
    2,
    Math.floor(maxFireSeats),
  );

  const polygonRadius = getFirePolygonRadius(vertexCount);

  /*
   * Make sure neighboring fires have enough room for their
   * complete seating polygons.
   */
  const minimumAnchorDistance = Math.max(
    MIN_FIRE_GROUP_RADIUS,
    polygonRadius * 2 + MIN_FIRE_GROUP_PADDING,
  );

  const fireCount = uniqueFireIds.length;

  const ringRadius =
    minimumAnchorDistance /
    (2 * Math.sin(Math.PI / fireCount));

  /*
   * Fire anchors themselves are distributed around a ring.
   * This does NOT affect the orientation of their seat polygons.
   */
  const angle =
    -Math.PI / 2 +
    (fireIndex * 2 * Math.PI) / fireCount;

  return {
    x: Math.round(Math.cos(angle) * ringRadius),
    y:
      FIRE_CENTER_Y +
      Math.round(Math.sin(angle) * ringRadius),
  };
};

/**
 * Returns a player's position around a fire.
 *
 * IMPORTANT:
 *
 * maxFireSeats = TOTAL polygon vertices.
 *
 * Vertex 0:
 *     HOST
 *     always at the top.
 *
 * Vertices 1..maxFireSeats-1:
 *     GUESTS
 *
 * The polygon is regular and has the SAME orientation
 * for every fire.
 */
export const getNightFireSeatPosition = (
  fireId: string,
  slot: number,
  maxFireSeats: number,
  fireIds: string[] = [],
): MapPoint => {
  const vertexCount = Math.max(
    2,
    Math.floor(maxFireSeats),
  );

  const anchor = getNightFireAnchor(
    fireId,
    fireIds,
    vertexCount,
  );

  const polygonRadius = getFirePolygonRadius(vertexCount);
  const seatRadius = slot === 0
    ? polygonRadius / 2
    : polygonRadius;

  /*
   * -PI / 2 means the first vertex is exactly at the top.
   *
   * Every subsequent vertex advances clockwise by the
   * same angular amount:
   *
   *     2PI / vertexCount
   */
  const vertexIndex =
    ((Math.floor(slot) % vertexCount) + vertexCount) %
    vertexCount;

  const angle =
    -Math.PI / 2 +
    (vertexIndex * 2 * Math.PI) / vertexCount;

  return {
    x:
      anchor.x +
      Math.round(Math.cos(angle) * seatRadius),

    y:
      anchor.y +
      Math.round(Math.sin(angle) * seatRadius),
  };
};

export const getPlayerMapPosition = (
  location: PlayerVisualLocation,
  mapData: MapDataDTO,
  playerIndex: number,
  hexSize = 38,
  fireIds: string[] = [],
  maxFireSeats = 3,
): MapPoint => {
  if (location.kind === "FIRE") {
    return getNightFireSeatPosition(
      location.id,
      location.slot,
      maxFireSeats,
      fireIds,
    );
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
      (candidate) =>
        candidate.development?.id === location.id,
    );

    if (tile) {
      const point = axialToIsometric(
        tile.q,
        tile.r,
        hexSize,
      );

      return {
        x: point.x,
        y: point.y,
      };
    }
  }

  if (location.kind === "TILE") {
    const tile = mapTiles(mapData).find(
      (candidate) => candidate.id === location.id,
    );

    if (tile) {
      const point = axialToIsometric(
        tile.q,
        tile.r,
        hexSize,
      );

      return {
        x: point.x,
        y: point.y,
      };
    }
  }

  return {
    x: (playerIndex % 5 - 2) * 38,
    y: 112 + Math.floor(playerIndex / 5) * 38,
  };
};