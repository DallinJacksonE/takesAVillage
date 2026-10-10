import React from "react";
import { ResearchTrainingBatchRow } from "../../presenters/ResearchPresenter";

import styles from "./TrainingProgressBadge.module.css";
interface TrainingProgressBadgeProps {
  batch: ResearchTrainingBatchRow;
}

export const TrainingProgressBadge: React.FC<TrainingProgressBadgeProps> = ({ batch }) => {
  if (batch.status === "stalled") {
    return <span title={batch.last_error || "Training session is stalled"} className={styles.text3}>Stalled</span>;
  }

  if (batch.status !== "running") {
    return <span className={styles.text3}>{batch.status}</span>;
  }

  const gameProgress = batch.games_per_generation
    ? ` · Game ${batch.current_generation_game_index || batch.games_completed || 0}/${batch.games_per_generation}`
    : "";
  const failureProgress = batch.games_failed ? ` · ${batch.games_failed} failed` : "";

  return (
    <span
      title={batch.progress_tooltip || "Training loop is running"}
      className={styles.text2}
    >
      <span aria-hidden="true" className={styles.text}>●</span>
      Running{gameProgress}{failureProgress}
    </span>
  );
};
