import { useGameState } from "./useGameState";
import { DevelopmentDTO } from "../../../../dtos/index";

export const usePlayerDevelopments = (playerId: string | undefined): DevelopmentDTO[] => {
  const gameState = useGameState();

  // Return an empty array if the game state isn't loaded or no ID is provided
  if (!playerId || !gameState?.developments) {
    return [];
  }

  // Safely filter the developments array by the owner's ID
  return gameState.developments.filter((dev: DevelopmentDTO) => dev?.owner_id === playerId);
};
