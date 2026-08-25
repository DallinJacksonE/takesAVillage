import React, { useState } from "react";
import { MapDataDTO, MapTileDTO, DevelopmentCostsDict, Phase, PublicPlayerDTO } from "../../dtos/index";
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
import { axialToIsometric, getNightFireSeatPosition, getPlayerMapPosition, getTradeGroupOffset } from "./mapGeometry";
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

  const developmentSprites: Record<string, string> = {
    Farm: "/images/sprites/developments/farm.png",
    Woods: "/images/sprites/developments/lumber-mill.png",
    Mine: "/images/sprites/developments/mine.png",
  };

  const getDevelopmentSprite = (type: string): string | undefined =>
    developmentSprites[type];

  return (
    <div
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
                {tile.development ? (
                  <img
                    src={getDevelopmentSprite(tile.development.type)}
                    alt=""
                    aria-hidden="true"
                    className={styles.developmentSprite}
                    draggable={false}
                  />
                ) : (
                  <span className={styles.field}>
                    {tile.type === "Farm" && <FontAwesomeIcon icon={faWheatAwn} />}
                    {tile.type === "Woods" && <FontAwesomeIcon icon={faTree} />}
                    {tile.type === "Mine" && <FontAwesomeIcon icon={faMountain} />}
                  </span>
                )}
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
          const center = getNightFireSeatPosition(fireId, 0, maxFireSeats, fireIds);
          const seatCount = Math.max(1, Math.floor(maxFireSeats));

          return (
            <React.Fragment key={`fire-group-${host.id}`}>
              {Array.from({ length: seatCount }, (_, seatIndex) => {
                const occupied = players.some(
                  (player) =>
                    player.visual_state.location.kind === "FIRE" &&
                    player.visual_state.location.id === fireId &&
                    player.visual_state.location.slot === seatIndex,
                );

                if (occupied) {
                  return null;
                }

                const seat = getNightFireSeatPosition(
                  fireId,
                  seatIndex,
                  seatCount,
                  fireIds,
                );
                const isHostSeat = seatIndex === 0;
                return (
                  <div
                    aria-label={isHostSeat
                      ? `Available host seat at ${getPlayerNameFromHook(host.id)}'s fire`
                      : `Available fire seat ${seatIndex} at ${getPlayerNameFromHook(host.id)}'s fire`}
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
