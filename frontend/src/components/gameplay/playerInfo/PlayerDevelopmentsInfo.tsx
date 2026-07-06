import React from "react";
import { usePlayers } from "../../hooks/usePlayerName";
import { DevelopmentDTO } from "../../../dtos/index";
import { useGameState } from "../../hooks/useGameState";

import styles from "./PlayerDevelopmentsInfo.module.css";
interface Props {
  playerId: string;
}

const PlayerDevelopmentsInfo: React.FC<Props> = ({ playerId }) => {
  const { players } = usePlayers();
  const gameState = useGameState();
  const player = players?.find((p) => p.id === playerId);

  if (!player) {
    return <></>;
  }

  return (
    <span>
      {player.developments &&
        gameState.developments
          // 1. Filter out developments that are not in the player's ID list
          .filter((dev: DevelopmentDTO) => player.developments.includes(dev.id))
          // 2. Map over the remaining developments
          .map((dev: DevelopmentDTO) => (
            <span key={dev.id} className={styles.text}>
              {dev.type} (L.{dev.level})
            </span>
          ))}
    </span>
  );
};

export default PlayerDevelopmentsInfo;
