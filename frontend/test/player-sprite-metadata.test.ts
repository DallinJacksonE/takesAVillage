import { getSpriteFramePosition } from "../src/components/gameplay/player/PlayerSprite/PlayerSprite";
import { getGoblinSpriteForAnimation } from "../src/components/gameplay/player/playerSpriteCatalog";

describe("sprite sheet metadata", () => {
  it("addresses frames across multiple rows", () => {
    expect(getSpriteFramePosition(22, 10, 96, 64)).toEqual({ x: -192, y: -128 });
  });

  it("maps authoritative WORK animations to matching goblin strips", () => {
    expect(getGoblinSpriteForAnimation("WORK_FARM").src).toContain("watering");
    expect(getGoblinSpriteForAnimation("WORK_WOODS").src).toContain("axe");
    expect(getGoblinSpriteForAnimation("WORK_MINE").src).toContain("mining");
    expect(getGoblinSpriteForAnimation("BUILD").columns).toBe(10);
  });

  it("maps accepted trades to the curated carry strip", () => {
    expect(getGoblinSpriteForAnimation("CARRY").src).toContain("carry");
  });
});
