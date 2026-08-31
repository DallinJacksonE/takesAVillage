import React, { useEffect, useRef, useState } from "react";
import {
  MapDataDTO,
  MapTileDTO,
  DevelopmentCostsDict,
  Phase,
  PublicPlayerDTO,
  DevelopmentDTO,
} from "../../dtos/index";
import { usePlayerName } from "../hooks/usePlayerName";
import PlayerInfo from "./playerInfo/PlayerInfo";
import { usePlayerColors } from "../hooks/usePlayerColor";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faWheatAwn,
  faTree,
  faMountain,
} from "@fortawesome/free-solid-svg-icons";
import styles from "./VillageMap.module.css";
import {
  axialToIsometric,
  getHexSlotForOccupantIndex,
  getNightFireSeatPosition,
  getPlayerMapPosition,
  getTradeGroupOffset,
} from "./mapGeometry";
import MapPlayerActor from "./player/MapPlayerActor";
import { getPhaseScene } from "./phaseScene";

interface Props {
  mapData: MapDataDTO;
  onBuild: (tileId: string) => void;
  playerId: string;
  development_costs: DevelopmentCostsDict;
  players: PublicPlayerDTO[];
  phase: Phase;
  onReact?: (emoji: "👍" | "❤️" | "😂" | "😠") => void;
  maxFireSeats?: number;
}

const VillageMap: React.FC<Props> = ({
  mapData,
  onBuild,
  playerId,
  development_costs,
  players,
  phase,
  onReact,
  maxFireSeats = 3,
}) => {
  const [selectedTile, setSelectedTile] = useState<MapTileDTO | null>(null);
  const mapCardRef = useRef<HTMLDivElement>(null);

  const [fireFit, setFireFit] = useState({
    scale: 1,
    x: 0,
    y: 0,
  });

  const getPlayerNameFromHook = usePlayerName();
  const { getPlayerColor } = usePlayerColors();
  const scene = getPhaseScene(phase);

  /*
   * maxFireSeats is the number of player seats in addition to
   * the host.
   *
   * Slot 0 = host
   * Slot 1..maxFireSeats = additional seats
   *
   * Therefore there are maxFireSeats + 1 total vertices/pips.
   */
  const totalFireSeats = Math.max(1, Math.floor(maxFireSeats) + 1);

  const tradeIds = players.flatMap((player) =>
    player.visual_state.location.kind === "TRADE"
      ? [player.visual_state.location.id]
      : []
  );

  const fireHosts = players.filter(
    (player) =>
      player.visual_state.location.kind === "FIRE" &&
      player.visual_state.location.slot === 0
  );

  const fireIds = fireHosts.flatMap((host) =>
    host.visual_state.location.kind === "FIRE"
      ? [host.visual_state.location.id]
      : []
  );

  useEffect(() => {
    if (phase !== "NIGHT") {
      setFireFit({
        scale: 1,
        x: 0,
        y: 0,
      });
      return;
    }

    const card = mapCardRef.current;

    if (!card || fireIds.length === 0) {
      return;
    }

    const fitFireLayout = () => {
      const width = card.clientWidth;
      const height = card.clientHeight;

      if (width <= 0 || height <= 0) {
        return;
      }

      const points: { x: number; y: number }[] = [];

      fireIds.forEach((fireId) => {
        /*
         * Render maxFireSeats + 1 total positions,
         * but pass maxFireSeats to the geometry function because
         * the geometry function itself adds the host vertex.
         */
        for (
          let seatIndex = 0;
          seatIndex < totalFireSeats;
          seatIndex++
        ) {
          const seat = getNightFireSeatPosition(
            fireId,
            seatIndex,
            maxFireSeats,
            fireIds
          );

          points.push({
            x: seat.x,
            y: seat.y,
          });
        }

        const fire = getNightFireSeatPosition(
          fireId,
          0,
          maxFireSeats,
          fireIds
        );

        points.push({
          x: fire.x,
          y: fire.y,
        });
      });

      if (points.length === 0) {
        setFireFit({
          scale: 1,
          x: 0,
          y: 0,
        });
        return;
      }

      let minX = Infinity;
      let maxX = -Infinity;
      let minY = Infinity;
      let maxY = -Infinity;

      for (const point of points) {
        minX = Math.min(minX, point.x);
        maxX = Math.max(maxX, point.x);
        minY = Math.min(minY, point.y);
        maxY = Math.max(maxY, point.y);
      }

      const FIT_PADDING = 55;

      const layoutWidth =
        maxX - minX + FIT_PADDING * 2;
      const layoutHeight =
        maxY - minY + FIT_PADDING * 2;

      const scale = Math.min(
        1,
        (width - FIT_PADDING * 2) / layoutWidth,
        (height - FIT_PADDING * 2) / layoutHeight
      );

      const centerX = (minX + maxX) / 2;
      const centerY = (minY + maxY) / 2;

      setFireFit({
        scale,
        x: -centerX * scale,
        y: -centerY * scale,
      });
    };

    fitFireLayout();

    const resizeObserver = new ResizeObserver(fitFireLayout);
    resizeObserver.observe(card);

    window.addEventListener("resize", fitFireLayout);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", fitFireLayout);
    };
  }, [phase, fireIds.join(","), maxFireSeats, totalFireSeats]);

  const HEX_SIZE = window.innerWidth * 0.045;
  const hexWidth = HEX_SIZE * Math.sqrt(3);
  const hexHeight = HEX_SIZE * 2;
  const DEVELOPMENT_SPRITE_SIZE = HEX_SIZE * 1;

  const pointyClipPath =
    "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)";

  const hexToPixel = (q: number, r: number) => {
    return axialToIsometric(q, r, HEX_SIZE);
  };

  const woodsBackground = "#267447";
  const farmBackground = "#D9AA3F";
  const mineBackground = "#687783";
  const openBorder = "#F5E6B8";
  const myBorder = "#5BE58A";

  const getTypeColor = (type: string) => {
    switch (type) {
      case "Farm":
        return farmBackground;
      case "Woods":
        return woodsBackground;
      case "Mine":
        return mineBackground;
      default:
        return "#e0e0e0";
    }
  };

  const getOwnerColor = (ownerId?: string) => {
    if (!ownerId) return openBorder;
    if (ownerId === playerId) return myBorder;
    return getPlayerColor(ownerId);
  };

  const getDevelopmentSprite = (
    development: DevelopmentDTO
  ): string | undefined => {
    const base = ({
      Farm: "farm",
      Woods: "lumber_mill",
      Mine: "mine",
    } as const)[development.type as "Farm" | "Woods" | "Mine"];

    if (!base) return undefined;

    const level = Math.max(1, Math.min(3, development.level || 1));
    return `/images/sprites/developments/${base}/level-${level}.png`;
  };

  return (
    <div
      ref={mapCardRef}
      className={`card ${styles.mapCard} ${styles.card}`}
      aria-label={scene.label}
      data-phase={scene.theme}
      onClick={() => setSelectedTile(null)}
    >
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          transformOrigin: "center center",
        }}
      >
        {scene.showAxialMap &&
          Object.values(mapData).map((tile) => {
            const { x, y } = hexToPixel(tile.q, tile.r);
            const isSelected =
              selectedTile?.id === tile.id;

            return (
              <div
                className={styles.hexTile}
                key={tile.id}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedTile(tile);
                }}
                style={{
                  position: "absolute",
                  left: x,
                  top: y,
                  width: hexWidth,
                  height: hexHeight,
                  background: tile.development
                    ? getOwnerColor(
                      tile.development.owner_id
                    )
                    : openBorder,
                  clipPath: pointyClipPath,
                  cursor: "pointer",
                  transform: `translate(-50%, -50%) ${isSelected
                    ? "scale(1.15)"
                    : "scale(1)"
                    }`,
                  transition:
                    "transform 0.15s ease-in-out",
                  zIndex: isSelected ? 10 : 1,
                }}
              >
                <div
                  className={styles.hexCore}
                  style={{
                    position: "absolute",
                    top: "4px",
                    left: "4px",
                    right: "4px",
                    bottom: "4px",
                    background: getTypeColor(tile.type),
                    clipPath: pointyClipPath,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexDirection: "column",
                    color: "#333",
                  }}
                >
                  {tile.development ? (
                    <img
                      src={getDevelopmentSprite(tile.development)}
                      alt=""
                      aria-hidden="true"
                      className={styles.developmentSprite}
                      draggable={false}
                      style={{
                        width: `${DEVELOPMENT_SPRITE_SIZE}px`,
                        height: `${DEVELOPMENT_SPRITE_SIZE}px`,
                      }}
                    />
                  ) : (
                    <span className={styles.field}>
                      {tile.type === "Farm" && (
                        <FontAwesomeIcon
                          icon={faWheatAwn}
                        />
                      )}
                      {tile.type === "Woods" && (
                        <FontAwesomeIcon
                          icon={faTree}
                        />
                      )}
                      {tile.type === "Mine" && (
                        <FontAwesomeIcon
                          icon={faMountain}
                        />
                      )}
                    </span>
                  )}
                </div>
              </div>
            );
          })}

        {!scene.showAxialMap && (
          <div className={styles.sceneTitle}>
            {scene.label}
          </div>
        )}

        {phase === "NIGHT" && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              pointerEvents: "none",
              transform: `translate(${fireFit.x}px, ${fireFit.y}px) scale(${fireFit.scale})`,
              transformOrigin: "center center",
            }}
          >
            {fireHosts.map((host) => {
              const fireId =
                host.visual_state.location.kind ===
                  "FIRE"
                  ? host.visual_state.location.id
                  : host.id;

              /*
               * Slot 0 is the host.
               * There are maxFireSeats + 1 total positions.
               *
               * IMPORTANT:
               * getNightFireSeatPosition receives maxFireSeats,
               * NOT totalFireSeats, because the geometry function
               * uses maxFireSeats to determine the polygon size.
               */
              const center =
                getNightFireSeatPosition(
                  fireId,
                  0,
                  maxFireSeats,
                  fireIds
                );

              return (
                <React.Fragment
                  key={`fire-group-${host.id}`}
                >
                  {Array.from(
                    { length: totalFireSeats },
                    (_, seatIndex) => {
                      const occupied =
                        players.some(
                          (player) =>
                            player.visual_state.location.kind ===
                            "FIRE" &&
                            player.visual_state.location.id ===
                            fireId &&
                            player.visual_state.location.slot ===
                            seatIndex
                        );

                      if (occupied) {
                        return null;
                      }

                      const seat =
                        getNightFireSeatPosition(
                          fireId,
                          seatIndex,
                          maxFireSeats,
                          fireIds
                        );

                      const isHostSeat =
                        seatIndex === 0;

                      return (
                        <div
                          aria-label={
                            isHostSeat
                              ? `Available host seat at ${getPlayerNameFromHook(
                                host.id
                              )}'s fire`
                              : `Available fire seat ${seatIndex} at ${getPlayerNameFromHook(
                                host.id
                              )}'s fire`
                          }
                          className={
                            styles.fireSeatDot
                          }
                          key={`fire-seat-${host.id}-${seatIndex}`}
                          style={{
                            left: seat.x,
                            top: seat.y,
                          }}
                        />
                      );
                    }
                  )}

                  <div
                    aria-label={`Campfire hosted by ${getPlayerNameFromHook(
                      host.id
                    )}`}
                    className={styles.campfire}
                    key={`fire-${host.id}`}
                    role="img"
                    style={{
                      left: center.x,
                      top: center.y + 35,
                    }}
                  />
                </React.Fragment>
              );
            })}
          </div>
        )}

        {players.map((player, index) => {
          const getPlayerTileId = (
            loc: typeof player.visual_state.location
          ): string | null => {
            if (loc.kind === "TILE") {
              return loc.id;
            }
            if (loc.kind === "DEVELOPMENT") {
              const tiles = Array.isArray(mapData)
                ? mapData
                : Object.values(mapData);
              const tile = tiles.find(
                (candidate) =>
                  candidate.development?.id === loc.id
              );
              return tile ? tile.id : null;
            }
            return null;
          };

          const tileId = getPlayerTileId(
            player.visual_state.location
          );
          const isHexLocation = tileId !== null;

          let hexSlot: number | undefined;
          if (isHexLocation) {
            if (
              player.visual_state.location.kind ===
              "TILE" ||
              player.visual_state.location.kind ===
              "DEVELOPMENT"
            ) {
              if (
                player.visual_state.location.slot !==
                undefined
              ) {
                hexSlot =
                  player.visual_state.location.slot;
              } else {
                const precedingPeers = players
                  .slice(0, index)
                  .filter(
                    (peer) =>
                      getPlayerTileId(
                        peer.visual_state.location
                      ) === tileId
                  ).length;
                hexSlot =
                  getHexSlotForOccupantIndex(
                    precedingPeers
                  );
              }
            }
          }

          const position = getPlayerMapPosition(
            player.visual_state.location,
            mapData,
            index,
            HEX_SIZE,
            fireIds,
            maxFireSeats,
            hexSlot
          );

          const tradeOffset =
            player.visual_state.location.kind ===
              "TRADE"
              ? getTradeGroupOffset(
                player.visual_state.location.id,
                tradeIds
              )
              : { x: 0, y: 0 };

          const locationKey = JSON.stringify(
            player.visual_state.location
          );

          const locationPeers = players
            .slice(0, index)
            .filter(
              (candidate) =>
                JSON.stringify(
                  candidate.visual_state.location
                ) === locationKey
            ).length;

          const isFireLocation =
            player.visual_state.location.kind ===
            "FIRE";

          const peerOffset = isFireLocation || isHexLocation
            ? { x: 0, y: 0 }
            : {
              x: locationPeers * 24,
              y: locationPeers * 8,
            };

          return (
            <MapPlayerActor
              color={getPlayerColor(player.id)}
              key={player.id}
              isLocal={player.id === playerId}
              onReact={
                player.id === playerId
                  ? onReact
                  : undefined
              }
              player={player}
              x={
                isFireLocation
                  ? (position.x +
                    tradeOffset.x +
                    peerOffset.x) *
                  fireFit.scale +
                  fireFit.x
                  : isHexLocation
                    ? position.x
                    : position.x +
                    tradeOffset.x +
                    peerOffset.x
              }
              y={
                isFireLocation
                  ? (position.y +
                    tradeOffset.y +
                    peerOffset.y) *
                  fireFit.scale +
                  fireFit.y
                  : isHexLocation
                    ? position.y
                    : position.y +
                    tradeOffset.y +
                    peerOffset.y
              }
            />
          );
        })}

        {selectedTile && (
          <div
            className="card"
            style={{
              fontSize: 15,
              position: "absolute",
              zIndex: 100,
              height: "65px",
              width: "115px",
              padding: "8px",
              boxShadow:
                "0 4px 15px rgba(0,0,0,0.2)",
              transform: "translate(-50%, -110%)",
              left: hexToPixel(
                selectedTile.q,
                selectedTile.r
              ).x,
              top: hexToPixel(
                selectedTile.q,
                selectedTile.r
              ).y,
              background: "white",
              cursor: "default",
            }}
            onMouseDown={(e) =>
              e.stopPropagation()
            }
          >
            <h4 className={styles.field2}>
              {selectedTile.type}
            </h4>

            {selectedTile.development ? (
              <div className={styles.field3}>
                <div>
                  <strong className={styles.field4}>
                    OWNER:
                  </strong>
                  <br />
                  <PlayerInfo
                    playerId={
                      selectedTile.development
                        .owner_id
                    }
                  />
                </div>

                {selectedTile.development.owner_id ===
                  playerId && (
                    <div className={styles.field5}>
                      This is your property.
                    </div>
                  )}
              </div>
            ) : (
              <div className={styles.field6}>
                <div className={styles.field7}>
                  Available for Development
                </div>

                <button
                  className={`btn-tooltip success ${styles.field8}`}
                  onClick={() => {
                    onBuild(selectedTile.id);
                    setSelectedTile(null);
                  }}
                >
                  Build:{" "}
                  {development_costs[
                    selectedTile.type
                  ]?.build
                    ? Object.entries(
                      development_costs[
                        selectedTile.type
                      ].build
                    )
                      .map(
                        ([resource, amount]) =>
                          `${amount} ${resource}`
                      )
                      .join(", ")
                    : "Unknown Cost"}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default VillageMap;