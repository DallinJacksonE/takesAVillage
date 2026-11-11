import { useEffect, useState, type CSSProperties, type MouseEvent } from "react";
import type { PublicPlayerDTO } from "../../../dtos";
import PlayerSprite from "./PlayerSprite";
import { getGoblinSpriteForAnimation } from "./playerSpriteCatalog";
import styles from "./MapPlayerActor.module.css";

export type PlayerReactionEmoji = "👍" | "❤️" | "😂" | "😠";

export interface MapPlayerActorProps {
  color: string;
  player: PublicPlayerDTO;
  x: number;
  y: number;
  onReact?: (emoji: PlayerReactionEmoji) => void;
  onClick?: () => void;
  isSelected?: boolean;
}

const WALK_TRANSITION_DURATION_MS = 550;

interface ReactionOption {
  readonly emoji: PlayerReactionEmoji;
  readonly label: string;
}

const REACTION_OPTIONS: readonly ReactionOption[] = [
  { emoji: "👍", label: "thumbs up" },
  { emoji: "❤️", label: "heart" },
  { emoji: "😂", label: "laughing" },
  { emoji: "😠", label: "angry" },
] as const;

const STATIC_ANIMATIONS: ReadonlySet<string> = new Set(["HURT", "DEAD"]);

const prefersReducedMotion = (): boolean =>
  typeof window !== "undefined" &&
  Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)").matches);

interface TransientPlayerSpriteProps {
  player: PublicPlayerDTO;
}

const TransientPlayerSprite = ({ player }: TransientPlayerSpriteProps) => {
  const shouldReduceMotion = prefersReducedMotion();
  const [isWalking, setIsWalking] = useState(
    !shouldReduceMotion && !STATIC_ANIMATIONS.has(player.visual_state.animation),
  );

  useEffect(() => {
    if (shouldReduceMotion) {
      setIsWalking(false);
      return;
    }

    const walkTimerId = window.setTimeout(
      () => setIsWalking(false),
      WALK_TRANSITION_DURATION_MS,
    );
    return () => window.clearTimeout(walkTimerId);
  }, [shouldReduceMotion]);

  const animation = isWalking ? "WALK" : player.visual_state.animation;
  const spriteMetadata = getGoblinSpriteForAnimation(animation);

  const isTargetTradePartner =
    player.visual_state.location.kind === "TRADE" &&
    player.visual_state.location.side === "TARGET";
  const direction = isTargetTradePartner ? "left" : "right";

  const isDeadAndPhaseFinished = animation === "DEAD" && player.finished_phase;
  const formattedAnimationName = animation.toLowerCase().replaceAll("_", " ");
  const spriteAltText = `${player.name}: ${formattedAnimationName}`;

  return (
    <PlayerSprite
      {...spriteMetadata}
      alt={spriteAltText}
      animation={animation}
      direction={direction}
      paused={isDeadAndPhaseFinished}
      scale={1.35}
    />
  );
};

const MapPlayerActor = ({
  color,
  player,
  x,
  y,
  onReact,
  onClick,
  isSelected,
}: MapPlayerActorProps) => {
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

    const reactionExpiryTimerId = window.setTimeout(
      () => setReactionVisible(false),
      remainingMs,
    );
    return () => window.clearTimeout(reactionExpiryTimerId);
  }, [player.reaction]);

  const actorStyle: CSSProperties = {
    "--player-color": color,
    left: x,
    top: y,
    cursor: onClick ? "pointer" : "default",
    transform: isSelected ? "translate(-50%, -75%) scale(1.1)" : undefined,
    zIndex: isSelected ? 10 : undefined,
    transition: "transform 0.15s ease-in-out",
  } as CSSProperties;

  const locationKey = JSON.stringify(player.visual_state.location);

  const isInteractive = Boolean(onClick || onReact);
  const hitboxClassName = [
    styles.hitboxOverlay,
    isInteractive && styles.interactive,
    onClick && styles.clickable,
  ]
    .filter(Boolean)
    .join(" ");

  const handleActorClick = (event: MouseEvent<HTMLDivElement>) => {
    if (onClick) {
      event.stopPropagation();
      onClick();
    }
  };

  const handleContextMenu = (event: MouseEvent<HTMLDivElement>) => {
    if (!onReact) {
      return;
    }
    event.preventDefault();
    setShowReactionMenu(true);
  };

  const handleReactionSelect = (
    event: MouseEvent<HTMLButtonElement>,
    emoji: PlayerReactionEmoji,
  ) => {
    event.stopPropagation();
    onReact?.(emoji);
    setShowReactionMenu(false);
  };

  return (
    <div
      className={styles.actor}
      onClick={handleActorClick}
      onContextMenu={handleContextMenu}
      style={actorStyle}
    >
      {reactionVisible && player.reaction && (
        <span aria-live="polite" className={styles.reaction}>
          {player.reaction.emoji}
        </span>
      )}

      {showReactionMenu && (
        <div
          aria-label="Choose a reaction"
          className={styles.reactionMenu}
          role="menu"
        >
          {REACTION_OPTIONS.map(({ emoji, label }) => (
            <button
              aria-label={`React with ${label}`}
              key={emoji}
              onClick={(event) => handleReactionSelect(event, emoji)}
              role="menuitem"
              type="button"
            >
              {emoji}
            </button>
          ))}
        </div>
      )}

      <span className={styles.name}>{player.name}</span>

      <div className={styles.spriteContainer}>
        <div className={styles.spritePresentation}>
          <TransientPlayerSprite key={locationKey} player={player} />
        </div>
        <div className={hitboxClassName} />
      </div>
    </div>
  );
};

export default MapPlayerActor;
