from service.game.actions import work
from service.game_manager.lifecycle import GameLifecycleService
from service.game_manager.persistence import persist_phase_completion
from service.game_manager.registry import GameRegistry


class RecordingSnapshotStore:
    def __init__(self):
        self.game = []
        self.work = []
        self.trade = []
        self.night = []

    def store_game_snapshot(self, *args):
        self.game.append(args)

    def store_work_snapshot(self, snapshot):
        self.work.append(snapshot)

    def store_trade_snapshot(self, snapshot):
        self.trade.append(snapshot)

    def store_night_snapshot(self, snapshot):
        self.night.append(snapshot)


def test_game_manager_persists_completed_phase_snapshots(make_game):
    game = make_game(training=False)
    store = RecordingSnapshotStore()

    persist_phase_completion(store, game, "WORK")
    persist_phase_completion(store, game, "TRADE")
    persist_phase_completion(store, game, "NIGHT")

    assert len(store.work) == len(game.players)
    assert len(store.trade) == len(game.players)
    assert len(store.night) == len(game.players)
    assert len(store.game) == 1
    assert store.game[0][0:3] == (game.id, game.day, "NIGHT")


def test_training_phase_snapshots_are_not_persisted(make_game):
    game = make_game(training=True)
    store = RecordingSnapshotStore()

    persist_phase_completion(store, game, "WORK")

    assert store.work == []


def test_manager_created_game_persists_each_phase_before_resolution(monkeypatch):
    store = RecordingSnapshotStore()
    monkeypatch.setattr(work.time, "sleep", lambda _seconds: None)
    registry = GameRegistry()
    lifecycle = GameLifecycleService(
        registry,
        phase_completion_callback=lambda game, phase: persist_phase_completion(
            store, game, phase),
    )

    game_id = lifecycle.create_game("host-1", "default")
    game = registry.get(game_id)
    try:
        game.add_player("host-1")
        game.start_game()

        game.next_phase()
        game.next_phase()
        game.next_phase()

        assert len(store.work) == 1
        assert len(store.trade) == 1
        assert len(store.game) == 1
        assert len(store.night) == 1
    finally:
        registry.remove(game_id)
