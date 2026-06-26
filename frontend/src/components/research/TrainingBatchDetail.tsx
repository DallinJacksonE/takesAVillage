import React from "react";
import { TrainingBatchDetailDTO } from "../../../../dtos";
import { ExpandableJsonPanel } from "./ExpandableJsonPanel";
import { VisualizationGallery } from "./VisualizationGallery";

interface TrainingBatchDetailProps {
  batch: TrainingBatchDetailDTO | null;
  onSelectGame(gameId: string): void;
}

export const TrainingBatchDetail: React.FC<TrainingBatchDetailProps> = ({ batch, onSelectGame }) => {
  if (!batch) {
    return <p style={{ color: "#888", fontStyle: "italic" }}>Select a training batch to inspect.</p>;
  }

  return (
    <div>
      <h2>Training Batch {batch.batch_id}</h2>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", marginBottom: "18px" }}>
        <Meta label="Status" value={batch.status} />
        {batch.ruleset && <Meta label="Ruleset" value={batch.ruleset} />}
        {batch.bot_model && <Meta label="Model" value={batch.bot_model} />}
        {batch.bot_count !== undefined && <Meta label="Bots" value={String(batch.bot_count)} />}
        {batch.current_generation !== undefined && <Meta label="Generation" value={`${batch.current_generation}${batch.total_generations ? ` / ${batch.total_generations}` : ""}`} />}
        {batch.current_game_id && <Meta label="Current Game" value={batch.current_game_id} />}
      </div>
      <VisualizationGallery visualizations={batch.visualizations} />

      <section style={{ marginTop: "18px" }}>
        <h3>Linked Games</h3>
        {batch.games?.length ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {batch.games.map((game) => (
              <button key={`${game.game_id}-${game.generation}`} className="btn btn-secondary" onClick={() => onSelectGame(game.game_id)}>
                Generation {game.generation}: {game.game_id}
              </button>
            ))}
          </div>
        ) : (
          <p style={{ color: "#888" }}>No linked games recorded yet.</p>
        )}
      </section>

      <section style={{ marginTop: "18px", overflowX: "auto" }}>
        <h3>Generation Stats</h3>
        {batch.generation_statistics?.length ? (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "2px solid #ddd" }}>
                <th>Generation</th>
                <th>Best</th>
                <th>Average</th>
                <th>Median</th>
                <th>Worst</th>
                <th>Survival</th>
              </tr>
            </thead>
            <tbody>
              {batch.generation_statistics.map((stats) => (
                <tr key={stats.generation} style={{ borderBottom: "1px solid #eee" }}>
                  <td>{stats.generation}</td>
                  <td>{stats.best_fitness}</td>
                  <td>{stats.average_fitness}</td>
                  <td>{stats.median_fitness ?? "-"}</td>
                  <td>{stats.worst_fitness ?? "-"}</td>
                  <td>{stats.survival_rate !== undefined ? `${Math.round(stats.survival_rate * 100)}%` : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ color: "#888" }}>No generation statistics yet.</p>
        )}
      </section>

      <ExpandableJsonPanel title="Raw batch data" data={batch} />
    </div>
  );
};

const Meta: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <span style={{ border: "1px solid #ddd", borderRadius: "999px", padding: "6px 10px", background: "#f8f8f8" }}>
    <strong>{label}:</strong> {value}
  </span>
);
