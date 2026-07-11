<<<<<<< HEAD
import React from "react";
import { TrainingBatchDetailDTO } from "../../dtos";
import { ExpandableJsonPanel } from "./ExpandableJsonPanel";
import { VisualizationGallery } from "./VisualizationGallery";

import styles from "./TrainingBatchDetail.module.css";
interface TrainingBatchDetailProps {
  batch: TrainingBatchDetailDTO | null;
  onSelectGame(gameId: string): void;
}

export const TrainingBatchDetail: React.FC<TrainingBatchDetailProps> = ({ batch, onSelectGame }) => {
  if (!batch) {
    return <p className={styles.copy3}>Select a training batch to inspect.</p>;
  }

  return (
    <div>
      <h2>Training Batch {batch.batch_id}</h2>
      <div className={styles.row}>
        <Meta label="Status" value={batch.status} />
        {batch.ruleset && <Meta label="Ruleset" value={batch.ruleset} />}
        {batch.bot_model && <Meta label="Model" value={batch.bot_model} />}
        {batch.bot_count !== undefined && <Meta label="Bots" value={String(batch.bot_count)} />}
        {batch.current_generation !== undefined && <Meta label="Generation" value={`${batch.current_generation}${batch.total_generations ? ` / ${batch.total_generations}` : ""}`} />}
        {batch.current_game_id && <Meta label="Current Game" value={batch.current_game_id} />}
      </div>
      <VisualizationGallery visualizations={batch.visualizations} />

      <section className={styles.section2}>
        <h3>Linked Games</h3>
        {batch.games?.length ? (
          <div className={styles.column}>
            {batch.games.map((game) => (
              <button key={`${game.game_id}-${game.generation}`} className="btn btn-secondary" onClick={() => onSelectGame(game.game_id)}>
                Generation {game.generation}: {game.game_id}
              </button>
            ))}
          </div>
        ) : (
          <p className={styles.copy2}>No linked games recorded yet.</p>
        )}
      </section>

      <section className={styles.section}>
        <h3>Generation Stats</h3>
        {batch.generation_statistics?.length ? (
          <table className={styles.table}>
            <thead>
              <tr className={styles.tr2}>
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
                <tr key={stats.generation} className={styles.tr}>
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
          <p className={styles.copy}>No generation statistics yet.</p>
        )}
      </section>

      <ExpandableJsonPanel title="Raw batch data" data={batch} />
    </div>
  );
};

const Meta: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <span className={styles.text}>
    <strong>{label}:</strong> {value}
  </span>
);
=======
import React from "react";
import { TrainingBatchDetailDTO } from "../../dtos";
import { ExpandableJsonPanel } from "./ExpandableJsonPanel";
import { VisualizationGallery } from "./VisualizationGallery";

import styles from "./TrainingBatchDetail.module.css";
interface TrainingBatchDetailProps {
  batch: TrainingBatchDetailDTO | null;
  onSelectGame(gameId: string): void;
}

export const TrainingBatchDetail: React.FC<TrainingBatchDetailProps> = ({ batch, onSelectGame }) => {
  if (!batch) {
    return <p className={styles.copy3}>Select a training batch to inspect.</p>;
  }

  const gamesByGeneration = (batch.games ?? []).reduce<Record<string, NonNullable<TrainingBatchDetailDTO["games"]>>>((groups, game) => {
    const key = String(game.generation);
    groups[key] = groups[key] ?? [];
    groups[key].push(game);
    return groups;
  }, {});

  const generationNumbers = Object.keys(gamesByGeneration)
    .map((generation) => Number(generation))
    .sort((left, right) => left - right);

  const sortedAttempts = (games: NonNullable<TrainingBatchDetailDTO["games"]>) =>
    games
      .map((game, index) => ({ game, index }))
      .sort((left, right) => (left.game.attempt ?? left.index + 1) - (right.game.attempt ?? right.index + 1));

  return (
    <div>
      <h2>Training Batch {batch.batch_id}</h2>
      <div className={styles.row}>
        <Meta label="Status" value={batch.status} />
        {batch.ruleset && <Meta label="Ruleset" value={batch.ruleset} />}
        {batch.bot_model && <Meta label="Model" value={batch.bot_model} />}
        {batch.bot_count !== undefined && <Meta label="Bots" value={String(batch.bot_count)} />}
        {batch.current_generation !== undefined && <Meta label="Generation" value={`${batch.current_generation}${batch.total_generations ? ` / ${batch.total_generations}` : ""}`} />}
        {batch.games_per_generation !== undefined && <Meta label="Games / Generation" value={String(batch.games_per_generation)} />}
        {batch.games_completed !== undefined && <Meta label="Games Finished This Gen" value={String(batch.games_completed)} />}
        {batch.games_failed !== undefined && batch.games_failed > 0 && <Meta label="Failed Games This Gen" value={String(batch.games_failed)} />}
        {batch.phase && <Meta label="Phase" value={batch.phase} />}
        {batch.last_heartbeat_at && <Meta label="Last Heartbeat" value={batch.last_heartbeat_at} />}
        {batch.last_error && <Meta label="Last Error" value={batch.last_error} />}
        {batch.current_game_id && <Meta label="Current Game" value={batch.current_game_id} />}
      </div>
      <VisualizationGallery visualizations={batch.visualizations} />

      <section className={styles.section2}>
        <h3>Training Game Attempts</h3>
        {batch.games?.length ? (
          <table aria-label="Training game attempts" className={styles.table}>
            <thead>
              <tr className={styles.tr2}>
                <th>Generation</th>
                <th>Attempt</th>
                <th>Status</th>
                <th>Genomes</th>
                <th>Best</th>
                <th>Average</th>
                <th>Error</th>
                <th>Open</th>
              </tr>
            </thead>
            <tbody>
              {generationNumbers.flatMap((generation) =>
                sortedAttempts(gamesByGeneration[String(generation)]).map(({ game, index }) => (
                  <tr key={`${game.game_id}-${game.generation}`} className={styles.tr}>
                    <td>Generation {generation}</td>
                    <td>{game.attempt ?? index + 1}</td>
                    <td>{game.status ?? "unknown"}</td>
                    <td>{game.genome_count ?? "-"}</td>
                    <td>{game.best_fitness ?? "-"}</td>
                    <td>{game.average_fitness ?? "-"}</td>
                    <td>{game.error_message ?? "-"}</td>
                    <td>
                      <button className="btn btn-secondary" onClick={() => onSelectGame(game.game_id)}>
                        Open game {game.game_id}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        ) : (
          <p className={styles.copy2}>No linked games recorded yet.</p>
        )}
      </section>

      <section className={styles.section}>
        <h3>Generation Stats</h3>
        {batch.generation_statistics?.length ? (
          <table className={styles.table}>
            <thead>
              <tr className={styles.tr2}>
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
                <tr key={stats.generation} className={styles.tr}>
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
          <p className={styles.copy}>No generation statistics yet.</p>
        )}
      </section>

      <ExpandableJsonPanel title="Raw batch data" data={batch} />
    </div>
  );
};

const Meta: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <span className={styles.text}>
    <strong>{label}:</strong> {value}
  </span>
);
>>>>>>> 5aae65484608285345edeb4ee838d500ef4f5a69
