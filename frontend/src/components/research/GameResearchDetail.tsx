import React from "react";
import { ResearchGameDetailDTO } from "../../dtos";
import { ExpandableJsonPanel } from "./ExpandableJsonPanel";
import { VisualizationGallery } from "./VisualizationGallery";

interface GameResearchDetailProps {
  game: ResearchGameDetailDTO | null;
}

export const GameResearchDetail: React.FC<GameResearchDetailProps> = ({ game }) => {
  if (!game) {
    return <p style={{ color: "#888", fontStyle: "italic" }}>Select a game to analyze.</p>;
  }

  return (
    <div>
      <h2>Game {game.game_id}</h2>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", marginBottom: "18px" }}>
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
  <span style={{ border: "1px solid #ddd", borderRadius: "999px", padding: "6px 10px", background: "#f8f8f8" }}>
    <strong>{label}:</strong> {value}
  </span>
);
