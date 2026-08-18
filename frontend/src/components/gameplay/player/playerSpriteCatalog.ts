const PLAYER_SPRITE_ROOT = "/images/sprites/players";

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
    fps: 8,
  },
  mining: {
    src: `${PLAYER_SPRITE_ROOT}/goblin/spr_mining_strip10.png`,
    frameWidth: 96,
    frameHeight: 64,
    frameCount: 10,
    fps: 8,
  },
} as const;
