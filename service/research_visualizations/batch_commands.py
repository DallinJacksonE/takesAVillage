from .command import VisualizationCommand
from .game_commands import _load_pyplot


class FitnessOverGenerationsCommand(VisualizationCommand):
    name = "fitness_over_generations"
    title = "Champion and Average Fitness Over Generations"
    description = "Line chart comparing champion fitness to average population fitness."

    def render(self, context):
        plt = _load_pyplot()
        stats = context.get("generation_statistics", []) or []
        generations = [entry.get("generation") for entry in stats]
        best = [entry.get("best_fitness", 0) for entry in stats]
        average = [entry.get("average_fitness", entry.get("median_fitness", 0)) for entry in stats]
        figure, axes = plt.subplots(figsize=(8, 4))
        axes.plot(generations, best, marker="o", label="Champion")
        axes.plot(generations, average, marker="o", label="Average")
        axes.set_title(self.title)
        axes.set_xlabel("Generation")
        axes.set_ylabel("Fitness")
        axes.legend()
        figure.tight_layout()
        return figure


class TradingAndContestingPerGameCommand(VisualizationCommand):
    name = "trading_and_contesting_per_game"
    title = "Trading, Lies and Contesting Per Game"
    description = "three-series chart of trade, lie, and contest counts by training game."

    def render(self, context):
        plt = _load_pyplot()
        games = context.get("games", []) or []
        labels = [game.get("game_id", str(index + 1)) for index, game in enumerate(games)]
        trades = [game.get("trade_count", 0) for game in games]
        lies = [game.get("lie_count", 0) for game in games]
        contests = [game.get("contest_count", 0) for game in games]
        x_positions = list(range(len(labels)))
        figure, axes = plt.subplots(figsize=(8, 4))
        trade_bars = axes.bar([x - 0.2 for x in x_positions], trades, width=0.2, label="Trades")
        lie_bars = axes.bar([x for x in x_positions], lies, width=0.2, label="Lies")
        contest_bars = axes.bar([x + 0.2 for x in x_positions], contests, width=0.2, label="Contests")
        axes.bar_label(trade_bars, padding=3)
        axes.bar_label(lie_bars, padding=3)
        axes.bar_label(contest_bars, padding=3)
        axes.set_xticks(x_positions, labels, rotation=30)
        axes.set_title(self.title)
        axes.set_xlabel("Game")
        axes.set_ylabel("Count")
        axes.legend()
        figure.tight_layout()
        return figure


def default_batch_visualization_commands():
    return [
        FitnessOverGenerationsCommand(),
        TradingAndContestingPerGameCommand(),
    ]
