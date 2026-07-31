from abc import ABC, abstractmethod
from typing import Any

class DatabaseProvider(ABC):
    @abstractmethod
    def create_user(self, user_uuid: str, consent_agreed: bool) -> bool: pass
    @abstractmethod
    def user_exists(self, user_uuid: str) -> bool: pass
    @abstractmethod
    def initialize_database(self): pass

    @abstractmethod
    def store_game_snapshot(self, game_id: str, day_num: int,
                            phase: str, snapshot_json: str): pass

    @abstractmethod
    def store_game_result(self, game_id: str, day_num: int,
                          phase: str, snapshot_json: str,
                          training_batch_id=None, training_generation=None,
                          game_type=None, trade_count=None,
                          contest_count=None, lie_count=None): pass

    @abstractmethod
    def get_all_game_history(self) -> list: pass
    @abstractmethod
    def get_all_games(self) -> list: pass
    @abstractmethod
    def store_visualization(self, game_id: str, plot_name: str, figure) -> Any: pass
    @abstractmethod
    def store_player_snapshot(self, game_id, day_num, phase, player): pass
    @abstractmethod
    def store_work_snapshot(self, snapshot): pass
    @abstractmethod
    def store_trade_snapshot(self, snapshot): pass
    @abstractmethod
    def store_night_snapshot(self, snapshot): pass
    @abstractmethod
    def store_genome(self, name: str, shorthand: str, genome_json: str): pass
    @abstractmethod
    def get_all_genomes(self) -> list: pass
    @abstractmethod
    def create_training_batch(self, batch_id: str, config: dict) -> bool: pass
    @abstractmethod
    def mark_training_batch_game_started(self, batch_id: str, game_id: str,
                                         generation: int,
                                         attempt: int | None = None): pass
    @abstractmethod
    def mark_training_batch_game_running(self, batch_id: str, game_id: str): pass
    @abstractmethod
    def mark_training_batch_game_failed(self, batch_id: str, game_id: str,
                                        error_message: str): pass
    @abstractmethod
    def mark_training_batch_game_completed(self, batch_id: str, game_id: str,
                                           genome_count: int,
                                           fitness_summary: dict | None = None): pass
    @abstractmethod
    def record_training_batch_heartbeat(self, batch_id: str, phase: str,
                                        current_generation: int,
                                        current_game_id: str | None = None): pass
    @abstractmethod
    def update_training_batch_status(self, batch_id: str, status: str,
                                     error_message: str | None = None): pass
    @abstractmethod
    def append_training_batch_generation_stats(self, batch_id: str,
                                               stats: dict): pass
    @abstractmethod
    def complete_training_batch(self, batch_id: str,
                                final_champion_genome_id: str | None = None): pass
    @abstractmethod
    def get_training_batches(self) -> list: pass
    @abstractmethod
    def get_training_batch(self, batch_id: str) -> dict | None: pass
    @abstractmethod
    def get_training_games(self, batch_id: str) -> list: pass
    @abstractmethod
    def store_research_visualization(self, scope_type: str, scope_id: str,
                                     name: str, title: str, mime_type: str,
                                     image_bytes: bytes,
                                     metadata: dict | None = None) -> Any: pass
    @abstractmethod
    def get_research_visualizations(self, scope_type: str,
                                    scope_id: str) -> list: pass
    @abstractmethod
    def get_research_visualization(self, visualization_id) -> Any: pass

# --- 2. The In-Memory Provider (Dev) ---


