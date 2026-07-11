import React from "react";
import { ResearchSortMode } from "../../service/ResearchService";

import styles from "./ResearchListSearch.module.css";
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
    <div className={styles.column}>
      <input
        type="search"
        placeholder="Search by id, type, ruleset, model..."
        value={searchQuery}
        onChange={(event) => onSearchChange(event.target.value)}
        className={styles.input}
      />
      <select
        value={sortMode}
        onChange={(event) => onSortChange(event.target.value as ResearchSortMode)}
        className={styles.input}
      >
        <option value="time_desc">Newest first</option>
        <option value="name_asc">Name A-Z</option>
        <option value="name_desc">Name Z-A</option>
      </select>
    </div>
  );
};
