import type { PlayerVisualAnimation } from "../../../dtos";

const PLAYER_SPRITE_ROOT = "/images/sprites/players";

export interface PlayerSpriteMetadata {
  src: string;
  frameWidth: number;
  frameHeight: number;
  frameCount: number;
  columns?: number;
  fps: number;
}

export const goblinPlayerSprites = {
  idle: {
    src: `${PLAYER_SPRITE_ROOT}/goblin/idle-strip9.png`,
    frameWidth: 96,
    frameHeight: 64,
    frameCount: 9,
    fps: 8,
  },
  hammer: {
    src: `${PLAYER_SPRITE_ROOT}/goblin/spr_hammering_strip23.png`,
    frameWidth: 96,
    frameHeight: 64,
    frameCount: 23,
    columns: 10,
    fps: 8,
  },
  mining: {
    src: `${PLAYER_SPRITE_ROOT}/goblin/spr_mining_strip10.png`,
    frameWidth: 96,
    frameHeight: 64,
    frameCount: 10,
    fps: 8,
  },
  watering: {
    src: `${PLAYER_SPRITE_ROOT}/goblin/spr_watering_strip5.png`,
    frameWidth: 96,
    frameHeight: 64,
    frameCount: 5,
    fps: 8,
  },
  axe: {
    src: `${PLAYER_SPRITE_ROOT}/goblin/spr_axe_strip10.png`,
    frameWidth: 96,
    frameHeight: 64,
    frameCount: 10,
    fps: 8,
  },
  attack: {
    src: `${PLAYER_SPRITE_ROOT}/goblin/spr_attack_strip10.png`,
    frameWidth: 96,
    frameHeight: 64,
    frameCount: 9,
    fps: 8,
  },
  walk: {
    src: `${PLAYER_SPRITE_ROOT}/goblin/spr_walk_strip8.png`,
    frameWidth: 96,
    frameHeight: 64,
    frameCount: 8,
    fps: 8,
  },
  carry: {
    src: `${PLAYER_SPRITE_ROOT}/goblin/spr_carry_strip8.png`,
    frameWidth: 96,
    frameHeight: 64,
    frameCount: 8,
    fps: 8,
  },
  hurt: {
    src: `${PLAYER_SPRITE_ROOT}/goblin/spr_hurt_strip8.png`,
    frameWidth: 96,
    frameHeight: 64,
    frameCount: 8,
    fps: 6,
  },
  death: {
    src: `${PLAYER_SPRITE_ROOT}/goblin/spr_death_strip13.png`,
    frameWidth: 96,
    frameHeight: 64,
    frameCount: 9,
    fps: 7,
  },
} as const;

export const getGoblinSpriteForAnimation = (
  animation: PlayerVisualAnimation,
): PlayerSpriteMetadata => {
  switch (animation) {
    case "WORK_FARM": return goblinPlayerSprites.watering;
    case "WORK_WOODS": return goblinPlayerSprites.axe;
    case "WORK_MINE": return goblinPlayerSprites.mining;
    case "BUILD": return goblinPlayerSprites.hammer;
    case "CONTEST": return goblinPlayerSprites.attack;
    case "WALK": return goblinPlayerSprites.walk;
    case "CARRY": return goblinPlayerSprites.carry;
    case "HURT": return goblinPlayerSprites.hurt;
    case "SICK": return goblinPlayerSprites.hurt;
    case "DEAD": return goblinPlayerSprites.death;
    default: return goblinPlayerSprites.idle;
  }
};
