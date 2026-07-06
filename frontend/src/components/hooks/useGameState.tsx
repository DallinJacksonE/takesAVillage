// components/hooks/useGameState.tsx
import React, { createContext, useContext, ReactNode } from "react";
import { GameStateDTO } from "../../dtos";

// 1. Create the Context
const GameStateContext = createContext<GameStateDTO | null>(null);

// 2. Create the Provider Component
interface GameStateProviderProps {
  gameState: GameStateDTO;
  children: ReactNode;
}

export const GameStateProvider: React.FC<GameStateProviderProps> = ({ gameState, children }) => {
  return (
    <GameStateContext.Provider value={gameState}>
      {children}
    </GameStateContext.Provider>
  );
};

// 3. Create the Custom Hook
export const useGameState = (): GameStateDTO => {
  const context = useContext(GameStateContext);
  if (!context) {
    throw new Error("useGameState must be used within a GameStateProvider");
  }
  return context;
};
