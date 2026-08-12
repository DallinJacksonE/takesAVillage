import type { JsonObject } from "../../db/contracts.js";
import { renderBarChart, renderLineChart } from "../svg.js";
import type { VisualizationCommand } from "./runner.js";

function records(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => !!item && typeof item === "object" && !Array.isArray(item)) : [];
}

const fitness: VisualizationCommand = {
  name: "fitness_over_generations",
  title: "Champion and Average Fitness Over Generations",
  description: "Line chart comparing champion fitness to average population fitness.",
  render(context) {
    const stats = records(context.generation_statistics);
    return renderLineChart({
      title: fitness.title,
      xLabel: "Generation",
      yLabel: "Fitness",
      series: [
        { name: "Champion", color: "#2b6cb0", points: stats.map((item) => ({ x: Number(item.generation ?? 0), y: Number(item.best_fitness ?? 0) })) },
        { name: "Average", color: "#2f855a", points: stats.map((item) => ({ x: Number(item.generation ?? 0), y: Number(item.average_fitness ?? item.median_fitness ?? 0) })) },
      ],
    });
  },
};

const activity: VisualizationCommand = {
  name: "trading_and_contesting_per_game",
  title: "Trading, Lies and Contesting Per Game",
  description: "Three-series chart of trade, lie, and contest counts by training game.",
  render(context) {
    const games = records(context.games);
    const labels = games.map((game, index) => String(game.game_id ?? index + 1));
    return renderBarChart({
      title: activity.title,
      xLabel: "Game",
      yLabel: "Count",
      labels,
      series: [
        { name: "Trades", color: "#3182ce", values: games.map((game) => Number(game.trade_count ?? 0)) },
        { name: "Lies", color: "#dd6b20", values: games.map((game) => Number(game.lie_count ?? 0)) },
        { name: "Contests", color: "#c53030", values: games.map((game) => Number(game.contest_count ?? 0)) },
      ],
    });
  },
};

export function defaultBatchVisualizationCommands(): VisualizationCommand[] { return [fitness, activity]; }
