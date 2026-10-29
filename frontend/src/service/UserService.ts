import {
  ActiveGamesDTO,
  ConsentDTO,
  JoinGameDTO,
  NewGameDTO,
  NewGameOptionsDTO
} from "../dtos";

export class UserService {
  async consent(): Promise<ConsentDTO | null> {
    try {
      const response = await fetch("/api/consent", { method: "POST" });
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error("Error sending consent:", error);
      return null;
    }
  }

  async getActiveGames(): Promise<ActiveGamesDTO> {
    try {
      const response = await fetch("/api/activeGames");
      if (response.ok) {
        const obj = await response.json();
        //console.log(obj);
        return obj;
      }
      return { games: [] };
    } catch (error) {
      console.error("Error fetching active games:", error);
      return { games: [] };
    }
  }

  async newGame(
    ruleset: string,
    botCount: number,
    botGenome: string = "random",
    botModel: string
  ): Promise<NewGameDTO | null> {
    try {
      console.log(
        "Creating game:",
        { ruleset, botCount, botGenome }
      );

      const response = await fetch("/api/newGame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ruleset,
          botCount,
          botGenome,
          botModel
        })
      });

      if (response.ok) {
        return await response.json();
      }

      return null;
    } catch (error) {
      console.error("Error starting game:", error);
      return null;
    }
  }

  async newGameOptions(): Promise<NewGameOptionsDTO | null> {
    try {
      const response = await fetch("/api/newGame", { method: "GET" });
      if (response.ok) {
        return await response.json();
      }
      return null;
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

      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error("Error joining game:", error);
      return null;
    }
  }
}
