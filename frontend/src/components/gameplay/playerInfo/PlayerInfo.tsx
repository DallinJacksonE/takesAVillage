import React, { useState, useRef, useEffect } from "react";
import { usePlayers } from "../../hooks/usePlayerName";
import { usePlayerColors } from "../../hooks/usePlayerColor";
import { usePlayerDevelopments } from "../../hooks/usePlayerDevelopments";
import { useGameState } from "../../hooks/useGameState";
import styles from "./PlayerInfo.module.css";
interface Props {
  playerId: string;
}

const PlayerInfo: React.FC<Props> = ({ playerId }) => {
  const { players } = usePlayers();
  const { getPlayerColor } = usePlayerColors();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLSpanElement>(null);
  const state = useGameState();

  // Find the specific player from the context array
  const player = players?.find((p) => p.id === playerId);
  const isUnderAttack = usePlayerDevelopments(player?.id)?.some(
    (dev: any) => dev.is_contested === true || dev.contest_initiator_id
  );
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
    return <span className={styles.text4}>Unknown Player</span>;
  }

  return (
    <span
      ref={containerRef}
      className={styles.text3}
    >
      {/* The Clickable Player Name */}
      <span
        onMouseOver={() => setIsOpen(!isOpen)}
        onMouseOut={() => setIsOpen(false)}
        style={{
          cursor: "pointer",
          fontWeight: "bold",
          color: getPlayerColor(player.id),
          textDecoration: "underline dotted",
          textUnderlineOffset: "3px",

          // Attack warning styling
          background: isUnderAttack
            ? "rgba(255,0,0,0.15)"
            : "transparent",

          border: isUnderAttack
            ? "1px solid rgba(255,0,0,0.5)"
            : "1px solid transparent",

          borderRadius: "6px",
          padding: "2px 6px",

          boxShadow: isUnderAttack
            ? "0 0 8px rgba(255,0,0,0.45)"
            : "none",

          transition: "all 0.2s ease",
        }}
      >
        {isUnderAttack && (
          <span
            className={styles.text2}
          >
            ⚔️
          </span>
        )}

        {getPlayerEmoji(player.health)} {player.name}
      </span>

      {/* The Floating Tooltip */}
      {isOpen && (
        <div
          className={styles.panel3}
          onClick={(e) => e.stopPropagation()} // Prevents clicks inside the tooltip from closing it
        >
          <h4 className={styles.header}>
            {player.name}
          </h4>

          {/* Health Status */}
          <div className={styles.panel2}>
            <strong>Health:</strong>{" "}
            <span className={player.health === "healthy" ? styles.healthGood : styles.healthBad}>
              {player.health ? player.health.toUpperCase() : "UNKNOWN"}
            </span>
          </div>

          {/* Developments List */}
          <div>
            <strong>Developments:</strong>
            {!player.developments || player.developments.length === 0 ? (
              <div className={styles.panel}>
                No developments yet.
              </div>
            ) : (
              <ul className={styles.list}>
                {player.developments.map((devId: string) => {
                  const dev = state.developments.find(
                    (d) => d.id === devId
                  );

                  if (!dev) return null;

                  return (
                    <li key={dev.id}>
                      {dev.type} (Lvl {dev.level})
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>
      )}
    </span>
  );
};



export default PlayerInfo;
