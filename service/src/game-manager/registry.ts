import type { Game } from "../game/game.js";

export class GameRegistry extends Map<string, Game> {
  add(gameId: string, game: Game): void { this.set(gameId, game); }
  create(game: Game): Game { this.set(game.id, game); return game; }
  list(): Game[] { return [...this.values()]; }
  remove(gameId: string): Game | undefined {
    const game = this.get(gameId);
    this.delete(gameId);
    return game;
  }
  contains(gameId: string): boolean { return this.has(gameId); }
}
