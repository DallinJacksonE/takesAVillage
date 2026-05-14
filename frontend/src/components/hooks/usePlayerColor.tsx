import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { PlayerDTO, GameStateDTO } from '../../../../dtos/index';

// 1. Define a palette of distinct colors for your players
const PLAYER_PALETTE: string[] = [
  "#0058C3", // Blue
  "#8B00B9", // Purple 
  "#007011",
  "#D10084",
  "#0012b2",
  "#8A561F",
  "#9A2A2A",
  "#7B9E89", // Teal
  "#CBEF43", // Lime
  "F038FF", // Magenta
];

const user_color = "#53CA6D"
// Define the shape of the Context
interface PlayerColorContextType {
  colorMap: Record<string, string>;
  getPlayerColor: (playerId: string) => string;
}

// 2. Create the Context with default empty values matching the Type
const PlayerColorContext = createContext<PlayerColorContextType>({
  colorMap: {},
  getPlayerColor: (playerId: string) => "#CCCCCC", // Fallback grey
});

// Define the Props for the Provider Component
interface PlayerColorProviderProps {
  children: ReactNode;
  gameState?: GameStateDTO | null; // Optional/Nullable depending on initial load state
}

// 3. Create the Provider Component
export const PlayerColorProvider: React.FC<PlayerColorProviderProps> = ({ children, gameState }) => {
  // Strongly type our state as a dictionary of strings
  const [colorMap, setColorMap] = useState<Record<string, string>>({});

  useEffect(() => {
    // The trick: Only run this if we have a player list AND the color map is currently empty.
    if (gameState?.player_list && Object.keys(colorMap).length === 0) {
      const newColorMap: Record<string, string> = {};

      gameState.player_list.forEach((player: PlayerDTO, index: number) => {
        if (player.id === gameState.me.id) {
          newColorMap[player.id] = user_color;
        } else {
          newColorMap[player.id] = PLAYER_PALETTE[index % PLAYER_PALETTE.length];
        }
      });

      setColorMap(newColorMap);
    }
  }, [gameState, colorMap]);

  // Helper function to easily grab a color by ID
  const getPlayerColor = (playerId: string): string => {
    return colorMap[playerId] || "var(--medium_grey)"; // Fallback if ID isn't found
  };

  return (
    <PlayerColorContext.Provider value={{ colorMap, getPlayerColor }}>
      {children}
    </PlayerColorContext.Provider>
  );
};

// 4. Create a custom hook for clean imports in your components
export const usePlayerColors = (): PlayerColorContextType => {
  return useContext(PlayerColorContext);
};
