import { useEffect, useState, type CSSProperties } from "react";
import styles from "./PlayerSprite.module.css";
import type { PlayerSpriteProps } from "./types";

type PlayerSpriteStyle = CSSProperties & {
  "--frame-height": number;
  "--frame-width": number;
  "--sprite-direction": 1 | -1;
  "--sprite-scale": number;
  "--sprite-src": string;
};

const DEFAULT_FPS = 8;
const DEFAULT_SCALE = 1;

export const getSpriteFramePosition = (
  frameIndex: number,
  columns: number,
  frameWidth: number,
  frameHeight: number,
) => ({
  x: -(frameIndex % columns) * frameWidth,
  y: -Math.floor(frameIndex / columns) * frameHeight,
});

const PlayerSprite = ({
  src,
  animation,
  frameWidth,
  frameHeight,
  frameCount,
  columns = frameCount,
  fps = DEFAULT_FPS,
  direction = "right",
  scale = DEFAULT_SCALE,
  paused = false,
  alt,
  className,
}: PlayerSpriteProps) => {
  const [frameIndex, setFrameIndex] = useState(0);
  const prefersReducedMotion =
    typeof window !== "undefined"
    && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

  useEffect(() => {
    setFrameIndex(0);
    if (paused || prefersReducedMotion || frameCount <= 1) return;
    const timer = window.setInterval(
      () => setFrameIndex((frame) => (frame + 1) % frameCount),
      1000 / fps,
    );
    return () => window.clearInterval(timer);
  }, [animation, fps, frameCount, paused, prefersReducedMotion]);

  const framePosition = getSpriteFramePosition(
    frameIndex,
    columns,
    frameWidth,
    frameHeight,
  );
  const spriteClassName = [
    styles.sprite,
    paused ? styles.paused : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  const style: PlayerSpriteStyle = {
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
      <div
        aria-hidden="true"
        className={styles.frameStrip}
        style={{ backgroundPosition: `${framePosition.x}px ${framePosition.y}px` }}
      />
    </div>
  );
};

export default PlayerSprite;
