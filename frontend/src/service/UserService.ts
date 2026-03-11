import { JoinableGame } from "../types/game";

export class UserService {
  async consent(): Promise<boolean> {
    try {
      const response = await fetch('/api/consent', { method: 'POST' });
      return response.ok;
    } catch (error) {
      console.error("Error sending consent:", error);
      return false;
    }
  }

  async getActiveGames(): Promise<JoinableGame[]> {
    try {
      const response = await fetch('/api/activeGames');
      if (response.ok) {
        return await response.json();
      }
      return [];
    } catch (error) {
      console.error("Error fetching active games:", error);
      return [];
    }
  }

  async newGame(): Promise<{ gameId: string } | null> {
    try {
      const response = await fetch('/api/newGame', { method: 'POST' });
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error("Error starting game:", error);
      return null;
    }
  }

  async joinGame(gameId: string): Promise<{ gameId: string } | null> {
    try {
      const response = await fetch('/api/joinGame', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gameId })
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
