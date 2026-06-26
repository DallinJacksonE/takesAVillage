import React from "react";
import { ResearchSortMode } from "../../service/ResearchService";

interface ResearchListSearchProps {
  searchQuery: string;
  sortMode: ResearchSortMode;
  onSearchChange(searchQuery: string): void;
  onSortChange(sortMode: ResearchSortMode): void;
}

export const ResearchListSearch: React.FC<ResearchListSearchProps> = ({
  searchQuery,
  sortMode,
  onSearchChange,
  onSortChange,
}) => {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "14px" }}>
      <input
        type="search"
        placeholder="Search by id, type, ruleset, model..."
        value={searchQuery}
        onChange={(event) => onSearchChange(event.target.value)}
        style={{ padding: "9px", border: "1px solid #ddd", borderRadius: "4px" }}
      />
      <select
        value={sortMode}
        onChange={(event) => onSortChange(event.target.value as ResearchSortMode)}
        style={{ padding: "9px", border: "1px solid #ddd", borderRadius: "4px" }}
      >
        <option value="time_desc">Newest first</option>
        <option value="name_asc">Name A-Z</option>
        <option value="name_desc">Name Z-A</option>
      </select>
    </div>
  );
};
