import React from "react";
import { ResearchTrainingBatchRow } from "../../presenters/ResearchPresenter";

import styles from "./TrainingProgressBadge.module.css";
interface TrainingProgressBadgeProps {
  batch: ResearchTrainingBatchRow;
}

export const TrainingProgressBadge: React.FC<TrainingProgressBadgeProps> = ({ batch }) => {
  if (batch.status !== "running") {
    return <span className={styles.text3}>{batch.status}</span>;
  }

  return (
    <span
      title={batch.progress_tooltip || "Training loop is running"}
      className={styles.text2}
    >
      <span aria-hidden="true" className={styles.text}>●</span>
      Running
    </span>
  );
};
