import React, { useContext } from "react";
import { PlayerDTO } from "@takes-a-village/shared";

interface PlayerContextType {
  players: PlayerDTO[];
}

export const PlayerContext = React.createContext<PlayerContextType | undefined>(
  undefined,
);

export const PlayerProvider: React.FC<{
  players: PlayerDTO[];
  children: React.ReactNode;
}> = ({ players, children }) =>
    React.createElement(PlayerContext.Provider, { value: { players } }, children);

export const usePlayerName = () => {
  // Destructure your players array from the context [cite: 161]
  const { players } = usePlayers();

  return (playerId: string | undefined): string => {
    // 1. Instantly catch undefined, null, or empty strings
    if (!playerId) return "Unknown Villager";

    // 2. Look up the player
    const player = players.find(p => p.id === playerId);

    // 3. Return their name, or a fallback if the ID isn't in the lobby
    return player ? player.name : "Unknown Villager";
  };
};

export const usePlayers = () => {
  const context = useContext(PlayerContext);
  if (context === undefined) {
    throw new Error("usePlayers must be used wtihin a PlayerProvider");
  }
  return context;
}

