import { useEffect, useRef, useState } from "react";
import { useGameState } from "../../hooks/useGameState";
import { usePlayerColors } from "../../hooks/usePlayerColor";
import { usePlayerDevelopments } from "../../hooks/usePlayerDevelopments";
import { usePlayers } from "../../hooks/usePlayerName";
import styles from "./PlayerInfo.module.css";

export interface PlayerInfoProps {
  playerId: string;
}

const HEALTH_EMOJIS: Record<string, string> = {
  healthy: "😎",
  sick: "🤧",
  recovering: "🤒",
  dead: "⚰️",
};

const getPlayerHealthEmoji = (health: string | undefined): string => {
  if (!health) return "🫥";
  return HEALTH_EMOJIS[health] ?? "🫥";
};

const PlayerInfo = ({ playerId }: PlayerInfoProps) => {
  const { players } = usePlayers();
  const { getPlayerColor } = usePlayerColors();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLSpanElement>(null);
  const gameState = useGameState();

  const player = players?.find((p) => p.id === playerId);
  const playerDevelopments = usePlayerDevelopments(player?.id);
  const isUnderAttack = playerDevelopments?.some(
    (dev) => dev.is_contested || Boolean(dev.contest_initiator_id),
  );

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  if (!player) {
    return <span className={styles.unknownPlayer}>Unknown Player</span>;
  }

  const playerNameClassName = `${styles.playerName} ${
    isUnderAttack ? styles.underAttack : ""
  }`;

  return (
    <span className={styles.container} ref={containerRef}>
      {/* Clickable / hoverable player trigger */}
      <span
        className={playerNameClassName}
        onClick={() => setIsOpen((prev) => !prev)}
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        role="button"
        style={{ color: getPlayerColor(player.id) }}
        tabIndex={0}
      >
        {isUnderAttack && <span className={styles.attackBadge}>⚔️</span>}
        {getPlayerHealthEmoji(player.health)} {player.name}
      </span>

      {/* Floating tooltip */}
      {isOpen && (
        <div
          aria-label={`${player.name} details`}
          className={styles.tooltipPopover}
          onClick={(event) => event.stopPropagation()}
          role="tooltip"
        >
          <h4 className={styles.tooltipHeader}>{player.name}</h4>

          <div className={styles.healthRow}>
            <strong>Health:</strong>{" "}
            <span
              className={
                player.health === "healthy" ? styles.healthGood : styles.healthBad
              }
            >
              {player.health ? player.health.toUpperCase() : "UNKNOWN"}
            </span>
          </div>

          <div>
            <strong>Developments:</strong>
            {!player.developments || player.developments.length === 0 ? (
              <div className={styles.emptyDevelopments}>No developments yet.</div>
            ) : (
              <ul className={styles.developmentsList}>
                {player.developments.map((devId) => {
                  const dev = gameState?.developments?.find((d) => d.id === devId);
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
