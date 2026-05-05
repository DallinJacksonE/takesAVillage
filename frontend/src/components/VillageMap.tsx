import React, { useState } from "react";
import { MapTileDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";
import PlayerInfo from "./PlayerInfo";

interface Props {
  mapData: MapTileDTO[];
  onAction: (action: string, payload: any) => void;
  playerId: string;
}

const VillageMap: React.FC<Props> = ({ mapData, onAction, playerId }) => {
  const [selectedTile, setSelectedTile] = useState<MapTileDTO | null>(null);
  const getPlayerNameFromHook = usePlayerName();

  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const HEX_SIZE = 50;

  const hexToPixel = (q: number, r: number) => {
    const x = HEX_SIZE * (Math.sqrt(3) * q + (Math.sqrt(3) / 2) * r);
    const y = HEX_SIZE * ((3 / 2) * r);
    return { x, y };
  };

  const getPlayerName = (id: string) => {
    if (id === playerId) {
      return "Your";
    }
    const name = getPlayerNameFromHook(id);
    return `${name}'s`;
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    setOffset({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  if (!mapData || mapData.length === 0) {
    return (
      <div style={{ padding: "20px", textAlign: "center", color: "#888" }}>
        Map generating...
      </div>
    );
  }

  return (
    <div
      className='card'
      style={{ height: "500px", display: "flex", flexDirection: "column" }}
    >
      <h3 style={{ borderBottom: "1px solid #eee", paddingBottom: "10px" }}>
        Village Map
      </h3>

      <div
        style={{
          flex: 1,
          position: "relative",
          overflow: "hidden",
          background: "#e0e5ec",
          cursor: isDragging ? "grabbing" : "grab",
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Map Viewport - Centered and Translated */}
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

            // Color based on type
            let bg = "#ccc";
            if (tile.type === "Farm") bg = "#8bc34a";
            if (tile.type === "Woods") bg = "#795548";
            if (tile.type === "Mine") bg = "#607d8b";

            return (
              <div
                key={tile.id}
                onClick={() => setSelectedTile(tile)}
                style={{
                  position: "absolute",
                  left: x,
                  top: y,
                  width: `${HEX_SIZE * 1.6}px`,
                  height: `${HEX_SIZE * 1.6}px`,
                  backgroundColor: bg,
                  clipPath:
                    "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: "pointer",
                  fontSize: "0.7rem",
                  color: "white",
                  fontWeight: "bold",
                  boxShadow: "inset 0 0 10px rgba(0,0,0,0.2)",
                  border:
                    selectedTile?.id === tile.id ? "3px solid white" : "none",
                  zIndex: 10,
                }}
              >
                {tile.type[0]}
              </div>
            );
          })}
        </div>

        {/* Floating Tooltip / Info Panel */}
        {selectedTile && (
          <div
            style={{
              position: "absolute",
              bottom: "20px",
              right: "20px",
              width: "200px",
              background: "white",
              padding: "15px",
              borderRadius: "8px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
              zIndex: 100,
            }}
          >
            <h4 style={{ margin: "0 0 5px 0" }}>{selectedTile.type} Plot</h4>
            <div style={{ fontSize: "0.85rem", color: "#666" }}>
              ID: {selectedTile.id}
              <br />
              Coords: {selectedTile.q}, {selectedTile.r}
            </div>
            <hr
              style={{
                margin: "10px 0",
                border: "0",
                borderTop: "1px solid #eee",
              }}
            />
            {selectedTile.owner_id ? (
              <div>
                <strong>Owner:</strong>
                <br />
                <PlayerInfo playerId={selectedTile.owner_id} />
              </div>
            ) : (
              <div
                style={{ display: "flex", flexDirection: "column", gap: "5px" }}
              >
                <div
                  style={{
                    color: "#2e7d32",
                    fontStyle: "italic",
                    marginBottom: "5px",
                  }}
                >
                  Available for Development
                </div>

                {/* NEW BUILD BUTTON */}
                <button
                  className='btn'
                  style={{
                    background: "#795548",
                    color: "white",
                    fontSize: "0.8rem",
                  }}
                  onClick={() => {
                    onAction("BUILD_DEV", { tile_id: selectedTile.id });
                    setSelectedTile(null); // Close popup after clicking
                  }}
                >
                  Build Dev (2 Wood)
                </button>
              </div>
            )}
            <button
              className='btn btn-secondary'
              style={{ marginTop: "10px", width: "100%", padding: "5px" }}
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
