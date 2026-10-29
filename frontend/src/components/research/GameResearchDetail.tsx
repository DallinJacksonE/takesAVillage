import React from "react";
import { ResearchGameDetailDTO } from "../../dtos";
import { ExpandableJsonPanel } from "./ExpandableJsonPanel";
import { VisualizationGallery } from "./VisualizationGallery";

import styles from "./GameResearchDetail.module.css";
interface GameResearchDetailProps {
  game: ResearchGameDetailDTO | null;
}

export const GameResearchDetail: React.FC<GameResearchDetailProps> = ({ game }) => {
  if (!game) {
    return <p className={styles.copy}>Select a game to analyze.</p>;
  }

  return (
    <div>
      <h2>Game {game.game_id}</h2>
      <div className={styles.row}>
        <Meta label="Type" value={game.game_type ?? "human"} />
        <Meta label="Created" value={new Date(game.created_at).toLocaleString()} />
        <Meta label="Day" value={String(game.day_num)} />
        <Meta label="Phase" value={game.phase} />
        {game.training_batch_id && <Meta label="Training Batch" value={game.training_batch_id} />}
        {game.training_generation !== undefined && game.training_generation !== null && (
          <Meta label="Generation" value={String(game.training_generation)} />
        )}
      </div>
      <VisualizationGallery visualizations={game.visualizations} />
      <ExpandableJsonPanel title="Parsed game data" data={game.data} />
    </div>
  );
};

const Meta: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <span className={styles.text}>
    <strong>{label}:</strong> {value}
  </span>
);
