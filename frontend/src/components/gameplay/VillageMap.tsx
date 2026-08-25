import React, { useEffect, useRef, useState } from "react";
import { MapDataDTO, MapTileDTO, DevelopmentCostsDict, Phase, PublicPlayerDTO } from "../../dtos/index";
import { usePlayerName } from "../hooks/usePlayerName";
import PlayerInfo from "./playerInfo/PlayerInfo";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faWheatAwn,
  faTree,
  faMountain,
  faHouseFlag
} from '@fortawesome/free-solid-svg-icons';
import { usePlayerColors } from "../hooks/usePlayerColor";
import styles from "./VillageMap.module.css";
import { axialToIsometric, getNightFireAnchor, getNightFireSeatPosition, getPlayerMapPosition, getTradeGroupOffset } from "./mapGeometry";
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

const VillageMap: React.FC<Props> = ({ mapData, onBuild, playerId, development_costs, players, phase, onReact, maxFireSeats = 3 }) => {
  const [selectedTile, setSelectedTile] = useState<MapTileDTO | null>(null);
  const [sceneScale, setSceneScale] = useState(1);
  const mapCardRef = useRef<HTMLDivElement | null>(null);
  const getPlayerNameFromHook = usePlayerName();
  const { getPlayerColor } = usePlayerColors();
  const scene = getPhaseScene(phase);
  const tradeIds = players.flatMap((player) => (
    player.visual_state.location.kind === "TRADE"
      ? [player.visual_state.location.id]
      : []
  ));
  const fireHosts = players.filter((player) => (
    player.visual_state.location.kind === "FIRE"
    && player.visual_state.location.slot === 0
  ));
  const fireIds = fireHosts.flatMap((host) => (
    host.visual_state.location.kind === "FIRE"
      ? [host.visual_state.location.id]
      : []
  ));

  // Correct Pointy-Topped Hex Math
  const HEX_SIZE = 38;
  const hexWidth = HEX_SIZE * Math.sqrt(3);
  const hexHeight = HEX_SIZE * 2;
  const pointyClipPath = "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)";

  const hexToPixel = (q: number, r: number) => {
    return axialToIsometric(q, r, HEX_SIZE);
  };

  // --- Styling Helpers ---

  const woodsBackground: string = "#267447";
  const farmBackground = "#D9AA3F";
  const mineBackground = "#687783";
  const openBorder = "#F5E6B8";
  const myBorder = "#5BE58A";

  // Keep the entire map/seat layout inside the visible card. The scene uses
  // absolute positioning, so its logical size can be larger than the card
  // when there are many fire seats or fires. Scale the scene uniformly rather
  // than allowing the top/bottom seats to be clipped.
  useEffect(() => {
    const card = mapCardRef.current;
    if (!card) return;

    const updateScale = () => {
      const width = card.clientWidth;
      const height = card.clientHeight;
      if (!width || !height) return;

      const padding = 24;
      const halfHexWidth = hexWidth / 2;
      const halfHexHeight = hexHeight / 2;
      let minX = -halfHexWidth;
      let maxX = halfHexWidth;
      let minY = -halfHexHeight;
      let maxY = halfHexHeight;

      for (const tile of Object.values(mapData)) {
        const point = hexToPixel(tile.q, tile.r);
        minX = Math.min(minX, point.x - halfHexWidth);
        maxX = Math.max(maxX, point.x + halfHexWidth);
        minY = Math.min(minY, point.y - halfHexHeight);
        maxY = Math.max(maxY, point.y + halfHexHeight);
      }

      if (phase === "NIGHT" && fireIds.length) {
        const seatCount = Math.max(2, Math.floor(maxFireSeats));
        const polygonRadius = Math.max(78, Math.ceil(150 / (2 * Math.sin(Math.PI / seatCount))));
        const firePadding = polygonRadius + 54;

        for (const fireId of fireIds) {
          const anchor = getNightFireAnchor(fireId, fireIds, seatCount);
          minX = Math.min(minX, anchor.x - firePadding);
          maxX = Math.max(maxX, anchor.x + firePadding);
          minY = Math.min(minY, anchor.y - firePadding);
          maxY = Math.max(maxY, anchor.y + firePadding);
        }
      }

      const contentWidth = Math.max(1, maxX - minX);
      const contentHeight = Math.max(1, maxY - minY);
      const availableWidth = Math.max(1, width - padding * 2);
      const availableHeight = Math.max(1, height - padding * 2);

      setSceneScale(Math.min(1, availableWidth / contentWidth, availableHeight / contentHeight));
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(card);
    return () => observer.disconnect();
  }, [mapData, phase, fireIds.join("|"), maxFireSeats, hexWidth, hexHeight]);

  const getTypeColor = (type: string) => {
    switch (type) {
      case "Farm": return farmBackground;
      case "Woods": return woodsBackground;
      case "Mine": return mineBackground;
      default: return "#e0e0e0";
    }
  };

  const getOwnerColor = (ownerId?: string) => {
    if (!ownerId) return openBorder;
    if (ownerId === playerId) return myBorder;
    return getPlayerColor(ownerId);
  };

  const getTileContents = (type: string, ownerId?: string): React.ReactNode => {
    if (ownerId) {
      return <FontAwesomeIcon icon={faHouseFlag} />;
    }

    switch (type) {
      case "Farm":
        return <FontAwesomeIcon icon={faWheatAwn} />;
      case "Woods":
        return <FontAwesomeIcon icon={faTree} />;
      case "Mine":
        return <FontAwesomeIcon icon={faMountain} />;
      default:
        return null;
    }
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
          transform: `translate(-50%, -50%) scale(${sceneScale})`,
          transformOrigin: "center center",
        }}
      >
        {scene.showAxialMap && Object.values(mapData).map((tile) => {
          const { x, y } = hexToPixel(tile.q, tile.r);
          const isSelected = selectedTile?.id === tile.id;

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
                background: tile.development ? getOwnerColor(tile.development.owner_id) : openBorder,
                clipPath: pointyClipPath,
                cursor: "pointer",
                transform: `translate(-50%, -50%) ${isSelected ? "scale(1.15)" : "scale(1)"}`,
                transition: "transform 0.15s ease-in-out",
                zIndex: isSelected ? 10 : 1,
              }}
            >
              <div
                className={styles.hexCore}
                style={{
                  position: "absolute",
                  top: "4px", left: "4px", right: "4px", bottom: "4px",
                  background: getTypeColor(tile.type),
                  clipPath: pointyClipPath,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexDirection: "column",
                  color: "#333",
                }}
              >
                <span className={styles.field}>
                  {getTileContents(tile.type, tile.development?.owner_id || "")}</span>
              </div>
            </div>
          );
        })}

        {!scene.showAxialMap && (
          <div className={styles.sceneTitle}>{scene.label}</div>
        )}

        {phase === "NIGHT" && fireHosts.map((host) => {
          const fireId = host.visual_state.location.kind === "FIRE"
            ? host.visual_state.location.id
            : host.id;
          const center = getNightFireAnchor(fireId, fireIds, maxFireSeats);
          const seatCount = Math.max(1, Math.floor(maxFireSeats));
          const occupiedSlots = new Set(
            players.flatMap((player) => {
              const location = player.visual_state.location;
              return location.kind === "FIRE" && location.id === fireId
                ? [location.slot]
                : [];
            }),
          );

          return (
            <React.Fragment key={`fire-group-${host.id}`}>
              {Array.from({ length: seatCount }, (_, seatIndex) => {
                // Seat 0 is always the host. Every other dot is only a
                // placeholder for a genuinely free seat.
                if (occupiedSlots.has(seatIndex)) {
                  return null;
                }

                const seat = getNightFireSeatPosition(
                  fireId,
                  seatIndex,
                  seatCount,
                  fireIds,
                );

                return (
                  <div
                    aria-label={`Free seat ${seatIndex + 1} at ${getPlayerNameFromHook(host.id)}'s fire`}
                    className={styles.fireSeatDot}
                    key={`fire-seat-${host.id}-${seatIndex}`}
                    style={{
                      left: seat.x,
                      top: seat.y,
                    }}
                  />
                );
              })}
              <div
                aria-label={`Campfire hosted by ${getPlayerNameFromHook(host.id)}`}
                className={styles.campfire}
                key={`fire-${host.id}`}
                role="img"
                style={{ left: center.x, top: center.y }}
              >
                🔥
              </div>
            </React.Fragment>
          );
        })}

        {players.map((player, index) => {
          const position = getPlayerMapPosition(
            player.visual_state.location,
            mapData,
            index,
            HEX_SIZE,
            fireIds,
            maxFireSeats,
          );
          const tradeOffset = player.visual_state.location.kind === "TRADE"
            ? getTradeGroupOffset(player.visual_state.location.id, tradeIds)
            : { x: 0, y: 0 };
          const locationKey = JSON.stringify(player.visual_state.location);
          const locationPeers = players.slice(0, index).filter(
            (candidate) => JSON.stringify(candidate.visual_state.location) === locationKey,
          ).length;
          const isFireLocation = player.visual_state.location.kind === "FIRE";
          const peerOffset = isFireLocation ? { x: 0, y: 0 } : { x: locationPeers * 24, y: locationPeers * 8 };

          return (
            <MapPlayerActor
              color={getPlayerColor(player.id)}
              key={player.id}
              isLocal={player.id === playerId}
              onReact={player.id === playerId ? onReact : undefined}
              player={player}
              x={position.x + tradeOffset.x + peerOffset.x}
              y={position.y + tradeOffset.y + peerOffset.y}
            />
          );
        })}

        {/* --- TOOLTIP POPUP --- */}
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
              boxShadow: "0 4px 15px rgba(0,0,0,0.2)",
              transform: "translate(-50%, -110%)",
              left: hexToPixel(selectedTile.q, selectedTile.r).x,
              top: hexToPixel(selectedTile.q, selectedTile.r).y,
              background: "white",
              cursor: "default",
            }}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <h4 className={styles.field2}>{selectedTile.type}</h4>

            {selectedTile.development ? (
              <div className={styles.field3}>
                <div>
                  <strong className={styles.field4}>OWNER:</strong>
                  <br />
                  <PlayerInfo playerId={selectedTile.development.owner_id} />
                </div>

                {selectedTile.development.owner_id === playerId && (
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
                  Build: {
                    development_costs[selectedTile.type]?.build
                      ? Object.entries(development_costs[selectedTile.type].build)
                        .map(([resource, amount]) => `${amount} ${resource}`)
                        .join(", ")
                      : "Unknown Cost"
                  }
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
