import { useEffect, useState, type CSSProperties } from "react";
import type { PublicPlayerDTO } from "../../../dtos";
import PlayerSprite from "./PlayerSprite";
import { getGoblinSpriteForAnimation } from "./playerSpriteCatalog";
import styles from "./MapPlayerActor.module.css";

interface Props {
  color: string;
  player: PublicPlayerDTO;
  x: number;
  y: number;
  isLocal?: boolean;
  onReact?: (emoji: "👍" | "❤️" | "😂" | "😠") => void;
}

const WALK_DURATION_MS = 550;
const REACTION_OPTIONS = [
  { emoji: "👍" as const, label: "thumbs up" },
  { emoji: "❤️" as const, label: "heart" },
  { emoji: "😂" as const, label: "laughing" },
  { emoji: "😠" as const, label: "angry" },
];

const prefersReducedMotion = () => (
  typeof window !== "undefined"
  && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
);

const TransientPlayerSprite = ({ player }: Pick<Props, "player">) => {
  const shouldReduceMotion = prefersReducedMotion();
  const [isWalking, setIsWalking] = useState(
    !shouldReduceMotion && !["HURT", "DEAD"].includes(player.visual_state.animation),
  );

  useEffect(() => {
    if (shouldReduceMotion) {
      setIsWalking(false);
      return;
    }

    const timer = window.setTimeout(() => setIsWalking(false), WALK_DURATION_MS);
    return () => window.clearTimeout(timer);
  }, [shouldReduceMotion]);

  const animation = isWalking ? "WALK" : player.visual_state.animation;
  const sprite = getGoblinSpriteForAnimation(animation);
  const direction = (
    player.visual_state.location.kind === "TRADE"
    && player.visual_state.location.side === "TARGET"
  ) ? "left" : "right";
  return (
    <PlayerSprite
      {...sprite}
      animation={animation}
      alt={`${player.name}: ${animation.toLowerCase().replaceAll("_", " ")}`}
      direction={direction}
      paused={animation === "DEAD" && player.finished_phase}
      scale={1.35}
    />
  );
};

const MapPlayerActor = ({ color, player, x, y, isLocal = false, onReact }: Props) => {
  const [showReactionMenu, setShowReactionMenu] = useState(false);
  const [reactionVisible, setReactionVisible] = useState(false);

  useEffect(() => {
    const reaction = player.reaction;
    if (!reaction) {
      setReactionVisible(false);
      return;
    }
    const remainingMs = Math.max(0, reaction.expires_at * 1000 - Date.now());
    setReactionVisible(remainingMs > 0);
    const timer = window.setTimeout(() => setReactionVisible(false), remainingMs);
    return () => window.clearTimeout(timer);
  }, [player.reaction]);

  const actorStyle = {
    "--player-color": color,
    left: x,
    top: y,
  } as CSSProperties;
  const locationKey = JSON.stringify(player.visual_state.location);

  return (
    <div
      className={`${styles.actor} ${isLocal ? styles.localActor : ""}`}
      onContextMenu={(event) => {
        if (!isLocal || !onReact) return;
        event.preventDefault();
        setShowReactionMenu(true);
      }}
      style={actorStyle}
    >
      {reactionVisible && player.reaction && (
        <span aria-live="polite" className={styles.reaction}>
          {player.reaction.emoji}
        </span>
      )}
      {showReactionMenu && (
        <div aria-label="Choose a reaction" className={styles.reactionMenu} role="menu">
          {REACTION_OPTIONS.map(({ emoji, label }) => (
            <button
              aria-label={`React with ${label}`}
              key={emoji}
              onClick={() => {
                onReact?.(emoji);
                setShowReactionMenu(false);
              }}
              role="menuitem"
              type="button"
            >
              {emoji}
            </button>
          ))}
        </div>
      )}
      <span className={styles.name}>{player.name}</span>
      <TransientPlayerSprite key={locationKey} player={player} />
    </div>
  );
};

export default MapPlayerActor;
