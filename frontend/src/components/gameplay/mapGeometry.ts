import type {
  MapDataDTO,
  PlayerVisualLocation,
} from "../../dtos";

export interface MapPoint {
  x: number;
  y: number;
}

const FIRE_CENTER_Y = 0;
const MIN_SEAT_CENTER_DISTANCE = 150;
const MIN_FIRE_GROUP_RADIUS = 64;
const MIN_FIRE_GROUP_PADDING = 120;

/**
 * maxFireSeats = number of GUEST seats.
 *
 * The host gets one additional vertex.
 *
 * Therefore:
 *
 *   vertexCount = maxFireSeats + 1
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

const mapTiles = (mapData: MapDataDTO) =>
  Array.isArray(mapData)
    ? mapData
    : Object.values(mapData);

/**
 * Returns the center position of a fire.
 *
 * Every fire is placed on the same large ring around
 * the map center, with enough separation for its
 * complete seating polygon.
 */
export const getNightFireAnchor = (
  fireId: string,
  fireIds: string[],
  vertexCount: number,
): MapPoint => {
  const uniqueFireIds = [...new Set(fireIds)].sort();
  const fireIndex = uniqueFireIds.indexOf(fireId);

  if (fireIndex < 0 || uniqueFireIds.length <= 1) {
    return {
      x: 0,
      y: FIRE_CENTER_Y,
    };
  }

  const polygonRadius =
    getFirePolygonRadius(vertexCount);

  /*
   * Make sure neighboring fires have enough room for
   * their complete seating polygons.
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
   * Fire anchors are distributed around a ring.
   *
   * Seat polygons themselves always have the same
   * orientation: host at the top.
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
 * maxFireSeats = number of GUEST seats.
 *
 * Therefore:
 *
 *   vertexCount = maxFireSeats + 1
 *
 * Vertex 0:
 *   HOST
 *
 * Vertices 1..maxFireSeats:
 *   GUESTS
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
  /*
   * The host occupies one vertex in addition to the
   * configured guest seats.
   */
  const vertexCount = Math.max(
    2,
    Math.floor(maxFireSeats) + 1,
  );

  const anchor = getNightFireAnchor(
    fireId,
    fireIds,
    vertexCount,
  );

  const polygonRadius =
    getFirePolygonRadius(vertexCount);

  /*
   * Every player should sit on the actual polygon vertex.
   *
   * Slot 0 = host
   * Slot 1 = guest 1
   * Slot 2 = guest 2
   * ...
   */
  const vertexIndex =
    ((Math.floor(slot) % vertexCount) + vertexCount) %
    vertexCount;

  /*
   * -PI / 2 means the first vertex is directly above
   * the fire.
   *
   * All fires use exactly the same orientation.
   */
  const angle =
    -Math.PI / 2 +
    (vertexIndex * 2 * Math.PI) / vertexCount;

  return {
    x:
      anchor.x +
      Math.round(
        Math.cos(angle) * polygonRadius,
      ),

    y:
      anchor.y +
      Math.round(
        Math.sin(angle) * polygonRadius,
      ),
  };
};

export const getPlayerMapPosition = (
  location: PlayerVisualLocation,
  mapData: MapDataDTO,
  playerIndex: number,
  hexSize = 38,
  fireIds: string[] = [],
  maxFireSeats: number,
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
      x:
        location.side === "INITIATOR"
          ? -54
          : 54,
      y: 12,
    };
  }

  if (location.kind === "DEVELOPMENT") {
    const tile = mapTiles(mapData).find(
      (candidate) =>
        candidate.development?.id === location.id,
    );

    if (tile) {
      return axialToIsometric(
        tile.q,
        tile.r,
        hexSize,
      );
    }
  }

  if (location.kind === "TILE") {
    const tile = mapTiles(mapData).find(
      (candidate) => candidate.id === location.id,
    );

    if (tile) {
      return axialToIsometric(
        tile.q,
        tile.r,
        hexSize,
      );
    }
  }

  return {
    x: (playerIndex % 5 - 2) * 38,
    y: 112 + Math.floor(playerIndex / 5) * 38,
  };
};