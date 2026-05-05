import React, { useContext } from "react";
import { PlayerDTO } from "../../../../dtos";

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
  const context = useContext(PlayerContext);
  if (context === undefined)
    throw new Error("usePlayerName must be used within a PlayerProvider");
  return (id: string) =>
    context.players.find((p) => p.id === id)?.name || id.substring(0, 4);
};

export const usePlayers = () => {
  const context = useContext(PlayerContext);
  if (context === undefined) {
    throw new Error("usePlayers must be used wtihin a PlayerProvider");
  }
  return context;
}
