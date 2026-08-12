import type { JsonObject } from "../../db/contracts.js";
import { renderBarChart, renderLineChart } from "../svg.js";
import type { VisualizationCommand } from "./runner.js";

type PlayerSnapshot = Record<string, unknown>;
type PlayersByDay = Record<string, Record<string, PlayerSnapshot>>;

function playersByDay(context: JsonObject): PlayersByDay {
  const data = context.data;
  if (!data || typeof data !== "object" || Array.isArray(data)) return {};
  const players = data.players;
  return players && typeof players === "object" && !Array.isArray(players) ? players as PlayersByDay : {};
}

function orderedDays(players: PlayersByDay): string[] { return Object.keys(players).sort((a, b) => Number(a) - Number(b)); }
function resources(snapshot: PlayerSnapshot): Record<string, number> {
  const value = snapshot.resources;
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, number> : {};
}

const inventory: VisualizationCommand = {
  name: "best_player_inventory_over_time",
  title: "Best Player Inventory Over Time",
  description: "Line chart of food, wood, and iron for the highest final-resource player.",
  render(context) {
    const snapshots = playersByDay(context);
    const days = orderedDays(snapshots);
    const finalPlayers = snapshots[days.at(-1) ?? ""] ?? {};
    const playerId = Object.keys(finalPlayers).sort((a, b) => {
      const total = (id: string) => Object.values(resources(finalPlayers[id] ?? {})).reduce((sum, value) => sum + Number(value || 0), 0);
      return total(b) - total(a);
    })[0] ?? "";
    return renderLineChart({
      title: inventory.title,
      xLabel: "Day",
      yLabel: "Inventory",
      series: ["food", "wood", "iron"].map((resource, index) => ({
        name: resource[0]!.toUpperCase() + resource.slice(1),
        color: ["#2f855a", "#8b5a2b", "#4a5568"][index]!,
        points: days.map((day) => ({ x: Number(day), y: Number(resources(snapshots[day]?.[playerId] ?? {})[resource] ?? 0) })),
      })),
    });
  },
};

const trades: VisualizationCommand = {
  name: "trades_per_player",
  title: "Trades Per Player",
  description: "Bar chart of completed trades by player.",
  render(context) {
    const snapshots = playersByDay(context);
    const finalPlayers = snapshots[orderedDays(snapshots).at(-1) ?? ""] ?? {};
    const labels = Object.keys(finalPlayers).sort();
    return renderBarChart({ title: trades.title, xLabel: "Player", yLabel: "Completed Trades", labels, series: [{ name: "Trades", color: "#3182ce", values: labels.map((id) => Number(finalPlayers[id]?.trade_count ?? 0)) }] });
  },
};

const developments: VisualizationCommand = {
  name: "developments_built",
  title: "Developments Built By Player",
  description: "Bar chart of final observed developments by player.",
  render(context) {
    const counts = new Map<string, number>();
    for (const players of Object.values(playersByDay(context))) for (const [id, snapshot] of Object.entries(players)) {
      const value = Array.isArray(snapshot.developments) ? snapshot.developments.length : 0;
      counts.set(id, Math.max(counts.get(id) ?? 0, value));
    }
    const labels = [...counts.keys()].sort();
    return renderBarChart({ title: developments.title, xLabel: "Player", yLabel: "Developments", labels, series: [{ name: "Developments", color: "#805ad5", values: labels.map((id) => counts.get(id) ?? 0) }] });
  },
};

const contests: VisualizationCommand = {
  name: "contests",
  title: "Contest Activity",
  description: "Bar chart of contest-like committed actions by day.",
  render(context) {
    const snapshots = playersByDay(context);
    const days = orderedDays(snapshots);
    const values = days.map((day) => Object.values(snapshots[day] ?? {}).filter((snapshot) => {
      const action = snapshot.committed_action;
      if (!action || typeof action !== "object" || Array.isArray(action)) return false;
      const command = String((action as Record<string, unknown>).action_command ?? (action as Record<string, unknown>).type ?? "").toUpperCase();
      return command.includes("CONTEST");
    }).length);
    return renderBarChart({ title: contests.title, xLabel: "Day", yLabel: "Contests", labels: days, series: [{ name: "Contests", color: "#c53030", values }] });
  },
};

export function defaultGameVisualizationCommands(): VisualizationCommand[] { return [inventory, trades, developments, contests]; }
