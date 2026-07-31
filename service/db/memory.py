import io
import json
from datetime import datetime

from service.db.contracts import DatabaseProvider
from service.logging import BackendLogger

db_logger = BackendLogger("db")

class InMemoryDB(DatabaseProvider):
    def __init__(self):
        self.users = {}
        self.history = []
        self.visualizations = {}
        self.genomes = []
        self.training_batches = {}
        self.research_visualizations = {}
        self.next_visualization_id = 1
        self.player_snapshots = []
        self.work_snapshots = []
        self.trade_snapshots = []
        self.night_snapshots = []

    def create_user(self, user_uuid: str, consent_agreed: bool) -> bool:
        self.users[user_uuid] = {
            "consent_agreed": consent_agreed,
            "created_at": datetime.now()
        }
        return True

    def user_exists(self, user_uuid: str) -> bool:
        return user_uuid in self.users

    def initialize_database(self):
        db_logger.info(
            "InMemoryDB ready. (Note: Data wipes on container restart)")
        
    def delete_research_visualizations(self, scope_type: str, scope_id: str):
        self.research_visualizations = {
            key: value
            for key, value in self.research_visualizations.items()
            if not (
                value["scope_type"] == scope_type
                and value["scope_id"] == scope_id
            )
        }

    def store_game_result(self, game_id, day_num, phase, snapshot_json,
                          training_batch_id=None, training_generation=None,
                          game_type=None, trade_count=None,
                          contest_count=None, lie_count=None):
        if isinstance(snapshot_json, str):
            data = json.loads(snapshot_json)
        else:
            data = snapshot_json

        self.history.append({
            "game_id": game_id,
            "day_num": day_num,
            "phase": phase,
            "data": data,
            "training_batch_id": training_batch_id,
            "training_generation": training_generation,
            "game_type": game_type or ("training" if training_batch_id else "human"),
            "trade_count": trade_count,
            "contest_count": contest_count,
            "lie_count": lie_count,
            "created_at": datetime.now()
        })

    def store_game_snapshot(self, game_id: str, day_num: int, phase: str, snapshot_json: str):
        self.history.append({
            "game_id": game_id,
            "day_num": day_num,
            "phase": phase,
            "data": json.loads(snapshot_json),
            "created_at": datetime.now()
        })

    def get_all_games(self):
        return sorted(self.history, key=lambda x: x['created_at'], reverse=True)

    def get_all_game_history(self) -> list:
        return sorted(self.history, key=lambda x: x['created_at'], reverse=True)

    def store_visualization(self, game_id: str, plot_name: str, figure):
        buf = io.BytesIO()
        figure.savefig(buf, format='png')
        buf.seek(0)

        if game_id not in self.visualizations:
            self.visualizations[game_id] = {}
        self.visualizations[game_id][plot_name] = buf.read()

    def store_player_snapshot(self, game_id, day_num, phase, player):
        self.player_snapshots.append({
            "game_id": game_id, "day_num": day_num, "phase": phase, "player": player
        })

    def store_work_snapshot(self, snapshot):
        self.work_snapshots.append(snapshot)

    def store_trade_snapshot(self, snapshot):
        self.trade_snapshots.append(snapshot)

    def store_night_snapshot(self, snapshot):
        self.night_snapshots.append(snapshot)

    def store_genome(self, name: str, shorthand: str, genome_json: str):
        self.genomes.append({
            "name": name,
            "shorthand_name": shorthand,
            "genome_data": json.loads(genome_json),
            "created_at": datetime.now()
        })

    def get_all_genomes(self) -> list:
        return sorted(self.genomes, key=lambda x: x['created_at'], reverse=True)

    def create_training_batch(self, batch_id: str, config: dict) -> bool:
        now = datetime.now()
        self.training_batches[batch_id] = {
            "batch_id": batch_id,
            "status": "running",
            "ruleset": config.get("ruleset"),
            "bot_model": config.get("bot_model"),
            "bot_count": config.get("bot_count"),
            "total_generations": config.get("total_generations"),
            "current_generation": 0,
            "current_game_id": None,
            "started_at": now,
            "completed_at": None,
            "last_heartbeat_at": now,
            "phase": "pending",
            "last_error": None,
            "base_genome_id": config.get("base_genome_id"),
            "final_champion_genome_id": None,
            "config": config.get("config", {}),
            "games_per_generation": (config.get("config", {}) or {}).get(
                "games_per_generation"),
            "games_completed": 0,
            "games_failed": 0,
            "generation_statistics": [],
            "games": [],
        }
        return True

    def mark_training_batch_game_started(self, batch_id: str, game_id: str,
                                         generation: int,
                                         attempt: int | None = None):
        batch = self.training_batches.get(batch_id)
        if not batch:
            return
        batch["status"] = "running"
        batch["current_game_id"] = game_id
        batch["current_generation"] = generation
        if not isinstance(batch.get("games"), list):
            batch["games"] = []
        batch["games"].append({
            "game_id": game_id,
            "generation": generation,
            "attempt": attempt,
            "status": "spawning",
            "error_message": None,
            "genome_count": 0,
            "best_fitness": None,
            "average_fitness": None,
        })

    def mark_training_batch_game_running(self, batch_id: str, game_id: str):
        batch = self.training_batches.get(batch_id)
        if not batch:
            return
        for game in batch.get("games", []):
            if game.get("game_id") == game_id:
                game["status"] = "running"
                return

    def mark_training_batch_game_failed(self, batch_id: str, game_id: str,
                                        error_message: str):
        batch = self.training_batches.get(batch_id)
        if not batch:
            return
        for game in batch.get("games", []):
            if game.get("game_id") == game_id:
                if game.get("status") != "failed":
                    batch["games_failed"] = int(batch.get("games_failed", 0) or 0) + 1
                game["status"] = "failed"
                game["error_message"] = error_message
                game["genome_count"] = int(game.get("genome_count", 0) or 0)
                batch["games_completed"] = len([
                    entry for entry in batch.get("games", [])
                    if entry.get("status") in ("completed", "failed", "skipped")
                ])
                return

    def mark_training_batch_game_completed(self, batch_id: str, game_id: str,
                                           genome_count: int,
                                           fitness_summary: dict | None = None):
        batch = self.training_batches.get(batch_id)
        if not batch:
            return
        summary = fitness_summary or {}
        for game in batch.get("games", []):
            if game.get("game_id") == game_id:
                game["status"] = "completed"
                game["error_message"] = None
                game["genome_count"] = int(genome_count or 0)
                game["best_fitness"] = summary.get("best_fitness")
                game["average_fitness"] = summary.get("average_fitness")
                batch["games_completed"] = len([
                    entry for entry in batch.get("games", [])
                    if entry.get("status") in ("completed", "failed", "skipped")
                ])
                batch["games_failed"] = len([
                    entry for entry in batch.get("games", [])
                    if entry.get("status") == "failed"
                ])
                return

    def record_training_batch_heartbeat(self, batch_id: str, phase: str,
                                        current_generation: int,
                                        current_game_id: str | None = None):
        batch = self.training_batches.get(batch_id)
        if not batch:
            return
        batch["last_heartbeat_at"] = datetime.now()
        batch["phase"] = phase
        batch["current_generation"] = current_generation
        batch["current_game_id"] = current_game_id

    def update_training_batch_status(self, batch_id: str, status: str,
                                     error_message: str | None = None):
        batch = self.training_batches.get(batch_id)
        if not batch:
            return
        batch["status"] = status
        batch["last_error"] = error_message
        if status in ("completed", "failed", "cancelled", "stalled"):
            batch["completed_at"] = datetime.now()

    def append_training_batch_generation_stats(self, batch_id: str, stats: dict):
        batch = self.training_batches.get(batch_id)
        if batch:
            batch.setdefault("generation_statistics", []).append(stats)

    def complete_training_batch(self, batch_id: str,
                                final_champion_genome_id: str | None = None):
        batch = self.training_batches.get(batch_id)
        if not batch:
            return
        batch["status"] = "completed"
        batch["completed_at"] = datetime.now()
        batch["final_champion_genome_id"] = final_champion_genome_id

    def get_training_batches(self) -> list:
        return sorted(
            [dict(batch) for batch in self.training_batches.values()],
            key=lambda batch: batch["started_at"], reverse=True)

    def get_training_batch(self, batch_id: str) -> dict | None:
        batch = self.training_batches.get(batch_id)
        return dict(batch) if batch else None

    def get_training_games(self, batch_id: str) -> list:
        batch = self.training_batches.get(batch_id)
        if not batch:
            return []
        return [dict(game) for game in batch.get("games", [])]

    def store_research_visualization(self, scope_type: str, scope_id: str,
                                     name: str, title: str, mime_type: str,
                                     image_bytes: bytes,
                                     metadata: dict | None = None):
        visualization_id = str(self.next_visualization_id)
        self.next_visualization_id += 1
        self.research_visualizations[visualization_id] = {
            "id": visualization_id,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "name": name,
            "title": title,
            "mime_type": mime_type,
            "image_bytes": image_bytes,
            "metadata": metadata or {},
            "created_at": datetime.now(),
        }
        return visualization_id

    def get_research_visualizations(self, scope_type: str, scope_id: str) -> list:
        visualizations = []
        for visualization in self.research_visualizations.values():
            if (visualization["scope_type"] == scope_type and
                    visualization["scope_id"] == scope_id):
                item = dict(visualization)
                item.pop("image_bytes", None)
                item["url"] = f"/api/research/visualizations/{item['id']}"
                visualizations.append(item)
        return sorted(visualizations, key=lambda item: item["created_at"])

    def get_research_visualization(self, visualization_id):
        visualization = self.research_visualizations.get(str(visualization_id))
        return dict(visualization) if visualization else None


# --- 3. The MySQL Provider (Prod) ---
