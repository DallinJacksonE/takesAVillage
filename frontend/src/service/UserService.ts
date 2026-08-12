import {
  activeGamesSchema,
  consentSchema,
  newGameOptionsSchema,
  newGameResponseSchema,
  type ActiveGamesDTO,
  type ConsentDTO,
  type JoinGameDTO,
  type NewGameDTO,
  type NewGameOptionsDTO,
} from "@takes-a-village/shared";

export class UserService {
  async consent(): Promise<ConsentDTO | null> {
    try {
      const response = await fetch("/api/consent", { method: "POST" });
      return response.ok ? consentSchema.parse(await response.json()) : null;
    } catch (error) {
      console.error("Error sending consent:", error);
      return null;
    }
  }

  async getActiveGames(): Promise<ActiveGamesDTO> {
    try {
      const response = await fetch("/api/activeGames");
      return response.ok ? activeGamesSchema.parse(await response.json()) : { games: [] };
    } catch (error) {
      console.error("Error fetching active games:", error);
      return { games: [] };
    }
  }

  async newGame(
    ruleset: string,
    botCount: number,
    botGenome = "random",
    botModel: string,
  ): Promise<NewGameDTO | null> {
    try {
      console.log("Creating game:", { ruleset, botCount, botGenome });
      const response = await fetch("/api/newGame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ruleset, botCount, botGenome, botModel }),
      });
      return response.ok ? newGameResponseSchema.parse(await response.json()) : null;
    } catch (error) {
      console.error("Error starting game:", error);
      return null;
    }
  }

  async newGameOptions(): Promise<NewGameOptionsDTO | null> {
    try {
      const response = await fetch("/api/newGame", { method: "GET" });
      return response.ok ? newGameOptionsSchema.parse(await response.json()) : null;
    } catch (error) {
      console.error("Error getting game options:", error);
      return null;
    }
  }

  async joinGame(gameId: string): Promise<JoinGameDTO | null> {
    try {
      const response = await fetch("/api/joinGame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ gameId }),
      });
      return response.ok ? newGameResponseSchema.parse(await response.json()) : null;
    } catch (error) {
      console.error("Error joining game:", error);
      return null;
    }
  }
}
