import React, { useState } from "react";
import { MapTileDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";
import PlayerInfo from "./PlayerInfo";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faWheatAwn, // Good for Farm
  faTree,     // Good for Woods
  faMountain, // Good for Mine
  faHouseFlag // Good for an owned development
} from '@fortawesome/free-solid-svg-icons';
interface Props {
  mapData: MapTileDTO[];
  onAction: (actionCommand: string, payload: any) => void;
  playerId: string;
}

const VillageMap: React.FC<Props> = ({ mapData, onAction, playerId }) => {
  const [selectedTile, setSelectedTile] = useState<MapTileDTO | null>(null);
  const getPlayerNameFromHook = usePlayerName();

  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Correct Pointy-Topped Hex Math
  const HEX_SIZE = 45;
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
    return opponentBorder;
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

  return (
    <div
      className="card"
      style={{
        height: "500px",
        position: "relative",
        overflow: "hidden",
        background: mapBackground,
        cursor: isDragging ? "grabbing" : "grab",
        userSelect: "none",
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: `translate(calc(-50% + ${offset.x}px), calc(-50% + ${offset.y}px))`,
        }}
      >
        {mapData.map((tile) => {
          const { x, y } = hexToPixel(tile.q, tile.r);
          const isSelected = selectedTile?.id === tile.id;

          return (
            <div
              key={tile.id}
              onClick={() => setSelectedTile(tile)}
              style={{
                position: "absolute",
                left: x,
                top: y,
                width: hexWidth,
                height: hexHeight,
                background: getOwnerColor(tile.owner_id),
                clipPath: pointyClipPath,
                cursor: "pointer",
                transform: `translate(-50%, -50%) ${isSelected ? "scale(1.15)" : "scale(1)"}`,
                transition: "transform 0.15s ease-in-out",
                zIndex: isSelected ? 10 : 1,
              }}
            >
              {/* Inner Hex to create colored border effect */}
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
                <span style={{ fontSize: "0.8rem", fontWeight: "bold", color: "white" }}>{getTileContents(tile.type, tile.owner_id)}</span>
              </div>
            </div>
          );
        })}

        {/* --- TOOLTIP POPUP --- */}
        {selectedTile && (
          <div
            className="card"
            style={{
              position: "absolute",
              zIndex: 100,
              width: "220px",
              padding: "15px",
              boxShadow: "0 4px 15px rgba(0,0,0,0.2)",
              transform: "translate(-50%, -110%)",
              left: hexToPixel(selectedTile.q, selectedTile.r).x,
              top: hexToPixel(selectedTile.q, selectedTile.r).y,
              background: "white",
              cursor: "default",
            }}
            onMouseDown={(e) => e.stopPropagation()} // Prevent dragging when clicking buttons
          >
            <h4 style={{ margin: "0 0 10px 0" }}>{selectedTile.type}</h4>

            {selectedTile.owner_id ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <div>
                  <strong style={{ fontSize: "0.8rem", color: "#666" }}>OWNER:</strong>
                  <br />
                  <PlayerInfo playerId={selectedTile.owner_id} />
                </div>

                {selectedTile.owner_id !== playerId && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "5px", marginTop: "5px" }}>
                    <button
                      className="btn success"
                      style={{ fontSize: "0.75rem", padding: "6px" }}
                      onClick={() => {
                        onAction("EMPLOYMENT", {
                          type: "EMPLOYMENT",
                          target_id: selectedTile.owner_id,
                          dev_id: selectedTile.id,
                          is_application: true,
                          wage: 1,
                          wage_type: "food",
                        });
                        setSelectedTile(null);
                      }}
                    >
                      Apply for Job
                    </button>
                    <button
                      className="btn danger"
                      style={{ fontSize: "0.75rem", padding: "6px" }}
                      onClick={() => {
                        onAction("CONTEST", {
                          type: "CONTEST",
                          target_id: selectedTile.owner_id,
                          dev_id: selectedTile.id,
                        });
                        setSelectedTile(null);
                      }}
                    >
                      Contest Ownership
                    </button>
                  </div>
                )}

                {selectedTile.owner_id === playerId && (
                  <div style={{ fontSize: "0.8rem", color: "#2196F3", fontStyle: "italic" }}>
                    This is your property.
                  </div>
                )}
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
                <div style={{ color: "#2e7d32", fontStyle: "italic", marginBottom: "5px", fontSize: "0.85rem" }}>
                  Available for Development
                </div>
                <button
                  className="btn"
                  style={{ background: "#795548", color: "white", fontSize: "0.8rem" }}
                  onClick={() => {
                    onAction("BUILD_DEV", { dev_id: selectedTile.id });
                    setSelectedTile(null);
                  }}
                >
                  Build Dev (2 Wood)
                </button>
              </div>
            )}

            <button
              className="btn btn-secondary"
              style={{ marginTop: "10px", width: "100%", padding: "5px", fontSize: "0.75rem" }}
              onClick={() => setSelectedTile(null)}
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default VillageMap;
