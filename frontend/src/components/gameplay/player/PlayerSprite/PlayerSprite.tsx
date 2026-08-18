import type { CSSProperties } from "react";
import styles from "./PlayerSprite.module.css";
import type { PlayerSpriteProps } from "./types";

type PlayerSpriteStyle = CSSProperties & {
  "--animation-duration": string;
  "--frame-count": number;
  "--frame-height": number;
  "--frame-width": number;
  "--sprite-direction": 1 | -1;
  "--sprite-scale": number;
  "--sprite-src": string;
};

const DEFAULT_FPS = 8;
const DEFAULT_SCALE = 1;

const PlayerSprite = ({
  src,
  animation,
  frameWidth,
  frameHeight,
  frameCount,
  fps = DEFAULT_FPS,
  direction = "right",
  scale = DEFAULT_SCALE,
  paused = false,
  alt,
  className,
}: PlayerSpriteProps) => {
  const durationSeconds = frameCount / fps;
  const spriteClassName = [
    styles.sprite,
    paused ? styles.paused : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  const style: PlayerSpriteStyle = {
    "--animation-duration": `${durationSeconds}s`,
    "--frame-count": frameCount,
    "--frame-height": frameHeight,
    "--frame-width": frameWidth,
    "--sprite-direction": direction === "right" ? 1 : -1,
    "--sprite-scale": scale,
    "--sprite-src": `url(${src})`,
  };

  return (
    <div
      aria-label={alt ?? `${animation} player sprite`}
      className={spriteClassName}
      role="img"
      style={style}
    >
      <div aria-hidden="true" className={styles.frameStrip} />
    </div>
  );
};

export default PlayerSprite;
