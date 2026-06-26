from .command import VisualizationCommand


def _load_pyplot():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except Exception as exc:
        raise RuntimeError("matplotlib is required to render research visualizations") from exc


def _player_resource_total(player_snapshot: dict) -> float:
    resources = player_snapshot.get("resources", {}) or {}
    return sum(float(resources.get(resource, 0) or 0) for resource in ("food", "wood", "iron"))


class BestPlayerInventoryOverTimeCommand(VisualizationCommand):
    name = "best_player_inventory_over_time"
    title = "Best Player Inventory Over Time"
    description = "Line chart of food, wood, and iron for the highest final-resource player."

    def render(self, context):
        plt = _load_pyplot()
        players_by_day = (context.get("data", {}) or {}).get("players", {}) or {}
        best_player_id = self._best_player_id(players_by_day)
        days = sorted(players_by_day.keys(), key=lambda day: int(day) if str(day).isdigit() else str(day))
        series = {"food": [], "wood": [], "iron": []}
        day_labels = []
        for day in days:
            snapshot = players_by_day.get(day, {}).get(best_player_id, {})
            resources = snapshot.get("resources", {}) or {}
            day_labels.append(int(day) if str(day).isdigit() else day)
            for resource in series:
                series[resource].append(resources.get(resource, 0) or 0)

        figure, axes = plt.subplots(figsize=(8, 4))
        for resource, values in series.items():
            axes.plot(day_labels, values, marker="o", label=resource.title())
        axes.set_title(self.title)
        axes.set_xlabel("Day")
        axes.set_ylabel("Inventory")
        axes.legend()
        figure.tight_layout()
        return figure

    def _best_player_id(self, players_by_day: dict) -> str:
        if not players_by_day:
            return ""
        final_day = sorted(players_by_day.keys(), key=lambda day: int(day) if str(day).isdigit() else str(day))[-1]
        final_players = players_by_day.get(final_day, {})
        if not final_players:
            return ""
        return max(final_players, key=lambda player_id: _player_resource_total(final_players[player_id]))


class TradesPerPlayerCommand(VisualizationCommand):
    name = "trades_per_player"
    title = "Trades Per Player"
    description = "Bar chart of trade history entries by player."

    def render(self, context):
        plt = _load_pyplot()
        players_by_day = (context.get("data", {}) or {}).get("players", {}) or {}
        trade_counts = {}
        for day_players in players_by_day.values():
            for player_id, snapshot in day_players.items():
                trade_counts[player_id] = trade_counts.get(player_id, 0) + len(snapshot.get("trade_history", []) or [])
        figure, axes = plt.subplots(figsize=(8, 4))
        axes.bar(list(trade_counts.keys()), list(trade_counts.values()))
        axes.set_title(self.title)
        axes.set_xlabel("Player")
        axes.set_ylabel("Trades")
        axes.tick_params(axis="x", rotation=30)
        figure.tight_layout()
        return figure


class DevelopmentsBuiltCommand(VisualizationCommand):
    name = "developments_built"
    title = "Developments Built By Player"
    description = "Bar chart of final observed developments by player."

    def render(self, context):
        plt = _load_pyplot()
        players_by_day = (context.get("data", {}) or {}).get("players", {}) or {}
        counts = {}
        for day_players in players_by_day.values():
            for player_id, snapshot in day_players.items():
                counts[player_id] = max(
                    counts.get(player_id, 0),
                    len(snapshot.get("developments", []) or []),
                )
        figure, axes = plt.subplots(figsize=(8, 4))
        axes.bar(list(counts.keys()), list(counts.values()))
        axes.set_title(self.title)
        axes.set_xlabel("Player")
        axes.set_ylabel("Developments")
        axes.tick_params(axis="x", rotation=30)
        figure.tight_layout()
        return figure


class ContestsCommand(VisualizationCommand):
    name = "contests"
    title = "Contest Activity"
    description = "Bar chart of contest-like committed actions by day."

    def render(self, context):
        plt = _load_pyplot()
        players_by_day = (context.get("data", {}) or {}).get("players", {}) or {}
        counts_by_day = {}
        for day, day_players in players_by_day.items():
            counts_by_day[day] = 0
            for snapshot in day_players.values():
                action = snapshot.get("committed_action") or {}
                command = str(action.get("action_command", action.get("type", ""))).upper()
                if "CONTEST" in command:
                    counts_by_day[day] += 1
        figure, axes = plt.subplots(figsize=(8, 4))
        axes.bar(list(counts_by_day.keys()), list(counts_by_day.values()))
        axes.set_title(self.title)
        axes.set_xlabel("Day")
        axes.set_ylabel("Contests")
        figure.tight_layout()
        return figure


def default_game_visualization_commands():
    return [
        BestPlayerInventoryOverTimeCommand(),
        TradesPerPlayerCommand(),
        DevelopmentsBuiltCommand(),
        ContestsCommand(),
    ]
