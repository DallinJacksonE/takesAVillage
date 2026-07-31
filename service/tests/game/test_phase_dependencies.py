from service.game import Game
from service.game.phases import Phase


class RecordingLogger:
    def info(self, *_args, **_kwargs):
        pass

    def warning(self, *_args, **_kwargs):
        pass


class DeterministicRandom:
    def choice(self, values):
        return values[0]

    def randint(self, _minimum, _maximum):
        return 2


class RecordingDispatcher:
    def __init__(self):
        self.actions = []

    def dispatch(self, game, user_id, data):
        self.actions.append((game.id, user_id, data))
        return "dispatched"


class RecordingPhaseResolver:
    def __init__(self):
        self.calls = []

    def start_day(self, game):
        self.calls.append(("start_day", game.day))

    def resolve_work(self, game):
        self.calls.append(("resolve_work", game.day))

    def resolve_night(self, game):
        self.calls.append(("resolve_night", game.day))


def test_game_uses_phase_constants_and_injected_clock_and_rng():
    game = Game(
        "game-1",
        "host-1",
        clock=lambda: 100.0,
        rng=DeterministicRandom(),
        logger=RecordingLogger(),
    )
    original_length = game.game_length

    game.add_player("player-1")
    game.start_game()

    assert game.phase == Phase.WORK.value
    assert game.phase_end_time == 100.0 + game.phase_length
    assert game.game_length == original_length + 2
    assert game.players["player-1"].name == game.rules.AVAILABLE_NAMES[0]


def test_game_delegates_actions_and_phase_rules_and_emits_completion():
    dispatcher = RecordingDispatcher()
    resolver = RecordingPhaseResolver()
    completed = []
    game = Game(
        "game-1",
        "host-1",
        clock=lambda: 100.0,
        rng=DeterministicRandom(),
        logger=RecordingLogger(),
        dispatcher=dispatcher,
        phase_resolver=resolver,
        on_phase_completed=lambda current_game, phase: completed.append(
            (current_game.id, phase)
        ),
    )
    game.add_player("player-1")
    game.start_game()

    result = game.handle_action(
        "player-1", {"action_command": "FINISH_PHASE"}
    )
    game.next_phase()

    assert result == "dispatched"
    assert dispatcher.actions[0][0:2] == ("game-1", "player-1")
    assert completed == [("game-1", Phase.WORK.value)]
    assert resolver.calls == [("start_day", 1), ("resolve_work", 1)]
    assert game.phase == Phase.TRADE.value
