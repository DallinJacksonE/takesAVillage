import React, { useState, useRef, useEffect } from "react";
import { usePlayers } from "./hooks/usePlayerName";
import { DevelopmentDTO } from "../../../dtos/index"

interface Props {
  playerId: string;
}

const PlayerInfo: React.FC<Props> = ({ playerId }) => {
  const { players } = usePlayers();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLSpanElement>(null);

  // Find the specific player from the context array
  const player = players?.find((p) => p.id === playerId);

  // Close the popup if the user clicks anywhere outside of it
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.addEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const getPlayerEmoji = (health: string) => {
    switch (health) {
      case "healthy": return "😎";
      case "sick": return "🤧";
      case "recovering": return "🤒";
      case "dead": return "⚰️"
      default: return "🫥";
    }
  }

  if (!player) {
    return <span style={{ color: "#999", fontStyle: "italic" }}>Unknown Player</span>;
  }

  return (
    <span
      ref={containerRef}
      style={{ position: "relative", display: "inline-block" }}
    >
      {/* The Clickable Player Name */}
      <span
        onClick={() => setIsOpen(!isOpen)}
        style={{
          cursor: "pointer",
          fontWeight: "bold",
          color: "#1976d2",
          textDecoration: "underline dotted rgba(25, 118, 210, 0.5)",
          textUnderlineOffset: "3px",
        }}
      >
        {getPlayerEmoji(player.health)} {player.name}

        {/* Removed extra {}, added implicit return to the map */}
        <span>
          {player.developments && player.developments.map((dev: DevelopmentDTO, index) => (
            <span key={index} style={{ marginLeft: "5px" }}>
              {dev.type}{dev.level}
            </span>
          ))}
        </span>
      </span>

      {/* The Floating Tooltip */}
      {isOpen && (
        <div
          style={{
            position: "absolute",
            bottom: "120%", // Floats directly above the name
            left: "50%",
            transform: "translateX(-50%)",
            width: "200px",
            background: "white",
            padding: "15px",
            borderRadius: "8px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            zIndex: 100,
            color: "#333",
            fontSize: "0.85rem",
            textAlign: "left",
            cursor: "default",
          }}
          onClick={(e) => e.stopPropagation()} // Prevents clicks inside the tooltip from closing it
        >
          <h4 style={{ margin: "0 0 10px 0", borderBottom: "1px solid #eee", paddingBottom: "5px" }}>
            {player.name}
          </h4>

          {/* Health Status */}
          <div style={{ marginBottom: "10px" }}>
            <strong>Health:</strong>{" "}
            <span style={{ color: player.health === "healthy" ? "#2e7d32" : "#c62828" }}>
              {player.health ? player.health.toUpperCase() : "UNKNOWN"}
            </span>
          </div>

          {/* Developments List */}
          <div>
            <strong>Developments:</strong>
            {!player.developments || player.developments.length === 0 ? (
              <div style={{ color: "#888", fontStyle: "italic", marginTop: "4px" }}>
                No developments yet.
              </div>
            ) : (
              <ul style={{ margin: "4px 0 0 0", paddingLeft: "20px" }}>
                {player.developments.map((dev: any, idx: number) => (
                  <li key={idx}>
                    {dev.type} (Lvl {dev.level})
                  </li>
                ))}
              </ul>
            )}
          </div>

          <button
            className="btn btn-secondary"
            style={{ marginTop: "10px", width: "100%", padding: "5px" }}
            onClick={() => setIsOpen(false)}
          >
            Close
          </button>
        </div>
      )}
    </span>
  );
};

export default PlayerInfo;
