import importlib

import pytest

from service.game.packet_handling.registry import (
    AUTO_FINISH_COMMANDS,
    COMMAND_HANDLERS,
    PHASE_LOCK_ALLOWED_COMMANDS,
)
from service.game.packet_handling.contracts import TradeContract
from service.game.packet_handling.dispatcher import PacketDispatcher
from service.game.models.development import Development
from service.game.state import events
from service.game.state.contracts import ContractTransition, validate_contract_transition
from service.game.state.event_registry import EVENT_APPLIERS
from service.game.state.health import transition_health
from service.game.state.legal_actions import get_legal_actions
from service.game.state.phases import PhaseMachine
from service.game.state.player_phase import PlayerPhaseState
from service.game.state.reducer import GameStateReducer


def test_health_transition_is_pure_and_returns_next_chance():
    rules = {
        "default": 0.1,
        "hunger_increase": 0.2,
        "cold_increase": 0.3,
        "recovery": 0.05,
    }

    result = transition_health(
        health="sick",
        sickness_chance=0.4,
        ate=True,
        warm=True,
        check=0.99,
        sickness_rules=rules,
    )

    assert result.health == "recovering"
    assert result.sickness_chance == pytest.approx(0.35)


def test_health_transition_dead_is_terminal_without_chance_mutation():
    rules = {
        "default": 0.1,
        "hunger_increase": 0.2,
        "cold_increase": 0.3,
        "recovery": 0.05,
    }

    result = transition_health(
        health="dead",
        sickness_chance=0.7,
        ate=False,
        warm=False,
        check=0.0,
        sickness_rules=rules,
    )

    assert result.health == "dead"
    assert result.sickness_chance == 0.7


def test_phase_machine_resolves_and_enters_next_phase(make_game):
    game = make_game()
    game.start_game()
    calls = []

    class RecordingResolver:
        @staticmethod
        def resolve_work(game_state):
            calls.append(("resolve", game_state.phase))

        @staticmethod
        def resolve_trade(game_state):
            calls.append(("resolve", game_state.phase))

        @staticmethod
        def resolve_night(game_state):
            calls.append(("resolve", game_state.phase))

        @staticmethod
        def start_day(game_state):
            calls.append(("enter", "WORK"))

    machine = PhaseMachine(RecordingResolver)

    machine.advance(game)

    assert calls == [("resolve", "WORK")]
    assert game.phase == "TRADE"
    assert game.day == 1

    machine.advance(game)

    assert calls[-1] == ("resolve", "TRADE")
    assert game.phase == "NIGHT"

    machine.advance(game)

    assert calls[-2:] == [("resolve", "NIGHT"), ("enter", "WORK")]
    assert game.phase == "WORK"
    assert game.day == 2


def test_game_next_phase_uses_explicit_phase_machine(make_game):
    game = make_game()
    game.start_game()
    game._phase_machine = type("FakeMachine", (), {
        "advance": lambda self, game_state: setattr(game_state, "phase", "TRADE")
    })()

    game.next_phase()

    assert game.phase == "TRADE"


def test_contract_transition_fsm_blocks_wrong_actor_and_terminal_updates():
    contract = TradeContract("player-1", "player-2", {"food": 1}, {})

    wrong_actor = validate_contract_transition(contract, "player-1", "ACCEPT")
    accepted = validate_contract_transition(contract, "player-2", "ACCEPT")
    contract.status = "FINALIZED"
    terminal = validate_contract_transition(contract, "player-2", "DENY")

    assert wrong_actor == ContractTransition(False, "WAITING_ON_OTHER_PLAYER")
    assert accepted == ContractTransition(True)
    assert terminal == ContractTransition(False, "TERMINAL_CONTRACT")


def test_get_legal_actions_reflects_phase_player_lock_and_development_state(make_game):
    game = make_game(player_ids=("player-1", "player-2"))
    game.start_game()
    owner = game.players["player-1"]
    worker = game.players["player-2"]
    owner.resources = {"food": 5, "wood": 5, "iron": 5}
    development = Development(
        "dev-1", "Farm", owner.session_id,
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    game.developments[development.id] = development
    owner.developments.append(development.id)
    worker.available_work = [{
        "development": development.to_dict(),
        "wage": 1,
        "wage_type": "food",
        "employer_id": owner.session_id,
        "action_id": None,
    }]

    owner_commands = {action["action_command"] for action in get_legal_actions(game, owner.session_id)}
    worker_commands = {action["action_command"] for action in get_legal_actions(game, worker.session_id)}
    worker.finished_phase = True
    locked_worker_commands = {action["action_command"] for action in get_legal_actions(game, worker.session_id)}

    assert {"BUILD_DEV", "UPGRADE_DEV", "MAINTAIN_DEV", "FINISH_PHASE"}.issubset(owner_commands)
    assert "COMMIT_WORK" in worker_commands
    assert locked_worker_commands == {"FINISH_PHASE"}


def test_player_phase_state_is_source_of_truth_for_finished_projection(make_game):
    game = make_game()
    game.start_game()
    player = game.players["player-1"]

    assert player.phase_state == PlayerPhaseState.ACTIVE.value
    assert player.finished_phase is False

    player.finished_phase = True

    assert player.phase_state == PlayerPhaseState.RESOLVED.value
    assert player.to_dict()["phase_state"] == PlayerPhaseState.RESOLVED.value


def test_intent_lifecycle_updates_explicit_player_phase_states(make_game):
    game = make_game()
    game.start_game()
    player = game.players["player-1"]

    game.set_intent(type("Intent", (), {
        "player_id": player.session_id,
        "committed_action": {"type": "TEST_INTENT"},
    })())

    assert player.phase_state == PlayerPhaseState.INTENT_SUBMITTED.value
    assert player.finished_phase is True

    game.clear_intent(player.session_id)

    assert player.phase_state == PlayerPhaseState.NEEDS_REPLACEMENT.value
    assert player.finished_phase is False


def test_every_domain_event_has_registered_state_applier():
    event_types = {
        event_type
        for event_type in vars(events).values()
        if isinstance(event_type, type)
        and getattr(event_type, "__module__", None) == events.__name__
    }

    assert event_types
    assert event_types <= set(EVENT_APPLIERS)


def test_state_reducer_appliers_are_split_by_domain_modules():
    modules = {
        "service.game.state.contract_reducer",
        "service.game.state.resource_reducer",
        "service.game.state.development_reducer",
        "service.game.state.phase_reducer",
        "service.game.state.campfire_reducer",
    }

    for module_name in modules:
        importlib.import_module(module_name)

    reducer_bases = {base.__name__ for base in GameStateReducer.__mro__}
    assert "ContractReducer" in reducer_bases
    assert "DevelopmentReducer" in reducer_bases


def test_action_command_policies_are_centralized_in_registry():
    assert PacketDispatcher.COMMAND_MAP is COMMAND_HANDLERS
    assert {
        "BUILD_DEV", "MAINTAIN_DEV", "UPGRADE_DEV", "COMMIT_WORK"
    } <= AUTO_FINISH_COMMANDS
    assert {
        "ACCEPT", "DENY", "CANCEL", "BARTER", "FINALIZE"
    } <= PHASE_LOCK_ALLOWED_COMMANDS
