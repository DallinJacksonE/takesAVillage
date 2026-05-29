import React, { useState } from "react";
import { useEffect, useRef } from "react";
import { MapTileDTO, DevelopmentCostsDict } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";
import PlayerInfo from "./PlayerInfo";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faWheatAwn,
  faTree,
  faMountain,
  faHouseFlag
} from '@fortawesome/free-solid-svg-icons';
import { usePlayerColors } from "./hooks/usePlayerColor";
interface Props {
  mapData: MapTileDTO[];
  onBuild: (tileId: string) => void;
  playerId: string;
  development_costs: DevelopmentCostsDict;
}

const VillageMap: React.FC<Props> = ({ mapData, onBuild, playerId, development_costs }) => {
  const [selectedTile, setSelectedTile] = useState<MapTileDTO | null>(null);
  const getPlayerNameFromHook = usePlayerName();
  const { getPlayerColor } = usePlayerColors();
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [scale, setScale] = useState(1);

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
    const x = HEX_SIZE * Math.sqrt(3) * (q + r / 2);
    const y = HEX_SIZE * (3 / 2) * r;
    return { x, y };
  };

  const getPlayerName = (id: string) => {
    if (id === playerId) return "Your";
    const name = getPlayerNameFromHook(id);
    return `${name}'s`;
  };

  // --- Styling Helpers ---

  const mapBackground: string = "#68503B";
  const woodsBackground: string = "#184E24";
  const farmBackground = "#AF9631";
  const mineBackground = "#4E5355";
  const openBorder = "#F7F3E3";
  const opponentBorder = "#F58066";
  const myBorder = "#53CA6D";

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
      className="card card-map_background"
      style={{
        width: "100%",
        boxSizing: "border-box",
        margin: "0 auto",
        height: "250px",
        position: "relative",
        overflow: "hidden",
        cursor: isDragging ? "grabbing" : "grab",
        userSelect: "none",
      }}
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
        {Object.values(mapData).map((tile) => {
          const { x, y } = hexToPixel(tile.q, tile.r);
          const isSelected = selectedTile?.id === tile.id;

          return (
            <div
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
                <span style={{ fontSize: "0.8rem", fontWeight: "bold", color: "white" }}>
                  {getTileContents(tile.type, tile.development?.owner_id || "")}</span>
              </div>
            </div>
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
            <h4 style={{ margin: "0 0 10px 0" }}>{selectedTile.type}</h4>

            {selectedTile.development ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <div>
                  <strong style={{ fontSize: "0.8rem", color: "#666" }}>OWNER:</strong>
                  <br />
                  <PlayerInfo playerId={selectedTile.development.owner_id} />
                </div>

                {selectedTile.development.owner_id === playerId && (
                  <div style={{ fontSize: "0.6rem", color: "#2196F3", fontStyle: "italic" }}>
                    This is your property.
                  </div>
                )}
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "5px", fontSize: ".06rem" }}>
                <div style={{ color: "#2e7d32", fontStyle: "italic", marginBottom: "5px", fontSize: "0.6rem" }}>
                  Available for Development
                </div>
                <button
                  className="btn-tooltip success"
                  style={{
                    fontSize: "0.6rem",
                    padding: "4px 6px"
                  }}
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
