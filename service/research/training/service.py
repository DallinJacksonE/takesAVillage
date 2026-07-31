from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from service.research.training import orchestrator
from service.research.training.presenter import build_training_session_payload
from service.research.training.session_store import TrainingSessionStore


@dataclass(frozen=True)
class TrainingConfig:
    ruleset: str = "default"
    bot_count: int = 5
    generations: int = 1
    base_genome_id: str = "random"
    bot_model: str = "genetic"
    mutation_strength: float = 0.25
    mutation_rate: float = 0.15
    random_immigrant_count: int = 1
    games_per_generation: int = 5

    def __post_init__(self):
        object.__setattr__(self, "games_per_generation", max(1, min(50, int(self.games_per_generation))))


class TrainingService:
    def __init__(self, database, game_factory, store=None,
                 bot_client_factory=None):
        self.database = database
        self.store = store or TrainingSessionStore()
        self.runtime = orchestrator.TrainingRuntime(
            database=database,
            game_factory=game_factory,
            bot_client_factory=bot_client_factory,
            sessions=self.store._runtime_sessions(),
        )

    async def start(self, config: TrainingConfig):
        return await orchestrator.start_training_session(
            self.runtime,
            config.ruleset, config.bot_count, config.generations,
            config.base_genome_id, config.bot_model,
            mutation_strength=config.mutation_strength,
            mutation_rate=config.mutation_rate,
            random_immigrant_count=config.random_immigrant_count,
            games_per_generation=config.games_per_generation,
        )

    async def cancel(self, session_id: str,
                     reason: str = "Training cancelled by operator") -> bool:
        return await orchestrator.cancel_training_session(
            self.runtime, session_id, reason)

    async def rerun(self, batch_id: str):
        batch = self.database.get_training_batch(batch_id)
        if not batch:
            return None
        options = batch.get("config", {}) or {}
        return await self.start(TrainingConfig(
            ruleset=batch.get("ruleset", "default"),
            bot_count=int(batch.get("bot_count") or 5),
            generations=int(batch.get("total_generations") or 1),
            base_genome_id=batch.get("base_genome_id") or "random",
            bot_model=batch.get("bot_model", "genetic"),
            mutation_strength=float(options.get("mutation_strength", 0.25)),
            mutation_rate=float(options.get("mutation_rate", 0.15)),
            random_immigrant_count=int(options.get("random_immigrant_count", 1)),
            games_per_generation=int(options.get("games_per_generation", 5)),
        ))

    def list(self):
        return build_training_session_payload(self.store.list())

    def status(self, session_id: str):
        return deepcopy(self.store.get(session_id))

    async def handle_game_ended(self, game_id: str, session_id: str):
        return await orchestrator.handle_training_game_ended(
            self.runtime, game_id, session_id)

    async def watchdog_loop(self, interval_seconds: int = 30,
                            stale_after_seconds: int = 600):
        return await orchestrator.training_watchdog_loop(
            self.runtime, interval_seconds, stale_after_seconds)

