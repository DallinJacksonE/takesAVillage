import React from "react";
import { ResearchGameListItemDTO } from "../../../../dtos";
import { ResearchTab, ResearchTrainingBatchRow } from "../../presenters/ResearchPresenter";
import { ResearchSortMode } from "../../service/ResearchService";
import { ResearchListSearch } from "./ResearchListSearch";
import { TrainingProgressBadge } from "./TrainingProgressBadge";

interface ResearchSidebarProps {
  activeTab: ResearchTab;
  searchQuery: string;
  sortMode: ResearchSortMode;
  games: ResearchGameListItemDTO[];
  trainingBatches: ResearchTrainingBatchRow[];
  selectedGameId?: string;
  selectedBatchId?: string;
  onTabChange(tab: ResearchTab): void;
  onSearchChange(searchQuery: string): void;
  onSortChange(sortMode: ResearchSortMode): void;
  onSelectGame(game: ResearchGameListItemDTO): void;
  onSelectTrainingBatch(batch: ResearchTrainingBatchRow): void;
}

export const ResearchSidebar: React.FC<ResearchSidebarProps> = ({
  activeTab,
  searchQuery,
  sortMode,
  games,
  trainingBatches,
  selectedGameId,
  selectedBatchId,
  onTabChange,
  onSearchChange,
  onSortChange,
  onSelectGame,
  onSelectTrainingBatch,
}) => {
  const visibleBatches = filterAndSortBatches(trainingBatches, searchQuery, sortMode);

  return (
    <div className="card" style={{ position: "sticky", top: "12px", maxHeight: "calc(100vh - 24px)", overflow: "auto" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginBottom: "14px" }}>
        <button className="btn" style={tabStyle(activeTab === "games")} onClick={() => onTabChange("games")}>Games</button>
        <button className="btn" style={tabStyle(activeTab === "training-batches")} onClick={() => onTabChange("training-batches")}>Training</button>
      </div>
      <ResearchListSearch
        searchQuery={searchQuery}
        sortMode={sortMode}
        onSearchChange={onSearchChange}
        onSortChange={onSortChange}
      />
      {activeTab === "games" ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {games.length === 0 && <p style={{ color: "#888" }}>No games found.</p>}
          {games.map((game) => (
            <button
              key={game.game_id}
              onClick={() => onSelectGame(game)}
              style={rowStyle(selectedGameId === game.game_id)}
            >
              <strong>{game.game_id}</strong>
              <span>{new Date(game.created_at).toLocaleString()}</span>
              <span>{game.game_type ?? "human"} • Day {game.day_num}</span>
              {game.training_batch_id && <span>Batch {game.training_batch_id.slice(0, 8)} • Gen {game.training_generation ?? "?"}</span>}
            </button>
          ))}
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {visibleBatches.length === 0 && <p style={{ color: "#888" }}>No training batches found.</p>}
          {visibleBatches.map((batch) => (
            <button
              key={batch.batch_id}
              onClick={() => onSelectTrainingBatch(batch)}
              title={batch.progress_tooltip}
              style={rowStyle(selectedBatchId === batch.batch_id)}
            >
              <strong>{batch.batch_id.slice(0, 12)}</strong>
              <TrainingProgressBadge batch={batch} />
              <span>{batch.ruleset ?? "unknown ruleset"} • {batch.bot_count ?? "?"} bots</span>
              <span>Generation {batch.current_generation ?? 0}{batch.total_generations ? ` / ${batch.total_generations}` : ""}</span>
              {batch.current_game_id && <span>Current game {batch.current_game_id}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

function filterAndSortBatches(
  batches: ResearchTrainingBatchRow[],
  searchQuery: string,
  sortMode: ResearchSortMode,
): ResearchTrainingBatchRow[] {
  const query = searchQuery.trim().toLowerCase();
  const filtered = query
    ? batches.filter((batch) => [batch.batch_id, batch.ruleset, batch.bot_model, batch.status]
      .some((value) => String(value ?? "").toLowerCase().includes(query)))
    : batches;

  return [...filtered].sort((a, b) => {
    if (sortMode === "name_asc") return a.batch_id.localeCompare(b.batch_id);
    if (sortMode === "name_desc") return b.batch_id.localeCompare(a.batch_id);
    return String(b.started_at ?? "").localeCompare(String(a.started_at ?? ""));
  });
}

function tabStyle(isActive: boolean): React.CSSProperties {
  return { backgroundColor: isActive ? "#2c3e50" : "#95a5a6" };
}

function rowStyle(isSelected: boolean): React.CSSProperties {
  return {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    padding: "10px",
    border: isSelected ? "2px solid #3498db" : "1px solid #ddd",
    borderRadius: "6px",
    background: isSelected ? "#eef7ff" : "white",
    textAlign: "left",
    color: "#222",
    cursor: "pointer",
  };
}
