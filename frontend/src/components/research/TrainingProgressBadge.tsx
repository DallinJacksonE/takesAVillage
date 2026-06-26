import React from "react";
import { ResearchTrainingBatchRow } from "../../presenters/ResearchPresenter";

interface TrainingProgressBadgeProps {
  batch: ResearchTrainingBatchRow;
}

export const TrainingProgressBadge: React.FC<TrainingProgressBadgeProps> = ({ batch }) => {
  if (batch.status !== "running") {
    return <span style={{ color: "#666", fontSize: "0.78rem" }}>{batch.status}</span>;
  }

  return (
    <span
      title={batch.progress_tooltip || "Training loop is running"}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        color: "#8e44ad",
        fontSize: "0.78rem",
        fontWeight: 600,
      }}
    >
      <span aria-hidden="true" style={{ display: "inline-block", animation: "pulse 1.2s infinite" }}>●</span>
      Running
    </span>
  );
};
