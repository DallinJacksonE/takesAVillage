import React, { useState } from "react";
import { useEffect, useRef } from "react";
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
import { axialToIsometric, getPlayerMapPosition, getTradeGroupOffset } from "./mapGeometry";
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
}

const VillageMap: React.FC<Props> = ({ mapData, onBuild, playerId, development_costs, players, phase, onReact }) => {
  const [selectedTile, setSelectedTile] = useState<MapTileDTO | null>(null);
  const getPlayerNameFromHook = usePlayerName();
  const { getPlayerColor } = usePlayerColors();
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [scale, setScale] = useState(1);
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

  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const stopScroll = (e: WheelEvent) => {
      e.preventDefault();
    };

    el.addEventListener("wheel", stopScroll, { passive: false });

    return () => {
      el.removeEventListener("wheel", stopScroll);
    };
  }, []);

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

  // --- Dragging Handlers ---
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
  };
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setOffset({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };
  const handleMouseUp = () => setIsDragging(false);

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    e.stopPropagation();

    setScale((prev) => {
      const next = prev - e.deltaY * 0.001;
      return Math.min(Math.max(next, 0.5), 2.5);
    });
  };

  return (
    <div
      ref={containerRef}
      className={`card ${styles.mapCard} ${styles.card}`}
      aria-label={scene.label}
      data-phase={scene.theme}
      style={{"--card-cursor": isDragging ? "grabbing" : "grab"} as React.CSSProperties}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
      onClick={() => setSelectedTile(null)}
    >
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: `
            translate(calc(-50% + ${offset.x}px), calc(-50% + ${offset.y}px))
            scale(${scale})
          `,
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
          const position = getPlayerMapPosition(
            host.visual_state.location,
            mapData,
            0,
            HEX_SIZE,
            fireIds,
          );
          return (
            <div
              aria-label={`Campfire hosted by ${getPlayerNameFromHook(host.id)}`}
              className={styles.campfire}
              key={`fire-${host.id}`}
              role="img"
              style={{ left: position.x, top: position.y + 34 }}
            >
              🔥
            </div>
          );
        })}

        {players.map((player, index) => {
          const position = getPlayerMapPosition(
            player.visual_state.location,
            mapData,
            index,
            HEX_SIZE,
            fireIds,
          );
          const tradeOffset = player.visual_state.location.kind === "TRADE"
            ? getTradeGroupOffset(player.visual_state.location.id, tradeIds)
            : { x: 0, y: 0 };
          const locationKey = JSON.stringify(player.visual_state.location);
          const locationPeers = players.slice(0, index).filter(
            (candidate) => JSON.stringify(candidate.visual_state.location) === locationKey,
          ).length;

          return (
            <MapPlayerActor
              color={getPlayerColor(player.id)}
              key={player.id}
              isLocal={player.id === playerId}
              onReact={player.id === playerId ? onReact : undefined}
              player={player}
              x={position.x + tradeOffset.x + locationPeers * 24}
              y={position.y + tradeOffset.y + locationPeers * 8}
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
