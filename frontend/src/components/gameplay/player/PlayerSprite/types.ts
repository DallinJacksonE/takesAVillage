import type { PlayerVisualAnimation } from "../../../../dtos";

export type PlayerSpriteAnimation =
  | "idle"
  | "walk"
  | "work"
  | "sick"
  | "dead"
  | PlayerVisualAnimation;

export type PlayerSpriteDirection = "left" | "right";

export interface PlayerSpriteProps {
  src: string;
  animation: PlayerSpriteAnimation;
  frameWidth: number;
  frameHeight: number;
  frameCount: number;
  columns?: number;
  fps?: number;
  direction?: PlayerSpriteDirection;
  scale?: number;
  paused?: boolean;
  alt?: string;
  className?: string;
}
