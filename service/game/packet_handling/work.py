import time

from service.game.packet_handling.base import Command
from service.game.packet_handling.contracts import TradeContract
from service.game.state.events import (
    ContractCreated,
    DevelopmentMaintained,
    DevelopmentUpgraded,
    PlayerResourcesGained,
    PlayerResourcesSpent,
)
from service.game.state.intents import MaintainIntent, UpgradeIntent, WorkIntent


DEVELOPMENT_OUTPUT = {"Farm": "food", "Woods": "wood", "Mine": "iron"}


class CommitWorkCommand(Command):
    def execute(self, game_state, player):
        if player.health in ["sick", "recovering", "dead"]:
            return False

        job_data = self.payload.get("job")
        if not job_data:
            return False

        dev_id = job_data.get("development", {}).get("id")
        live_dev = game_state.developments.get(dev_id)
        if not live_dev or getattr(live_dev, "is_contested", False):
            return False

        game_state.set_intent(WorkIntent(player.session_id, dev_id, job_data))
        return True


def resolve_work_phase(game_state):
    _resolve_development_intents(game_state)
    _resolve_work_intents(game_state)


def assign_default_work_intents(game_state):
    """Assign timeout WORK intents for healthy players with no chosen intent."""
    for player in game_state.players.values():
        if player.health in ["sick", "recovering", "dead"]:
            continue
        if game_state.get_intent(player.session_id) is not None:
            continue
        development = _highest_level_workable_development(game_state, player)
        if not development:
            continue
        game_state.set_intent(WorkIntent(
            player.session_id,
            development.id,
            _work_job_for_development(development),
        ))


def _highest_level_workable_development(game_state, player):
    candidates = [
        development
        for development in game_state.developments.values()
        if development.owner == player.session_id
        and not getattr(development, "is_contested", False)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda development: development.level)


def _work_job_for_development(development):
    resource = DEVELOPMENT_OUTPUT.get(development.type, "food")
    return {
        "development": development.to_dict(),
        "wage": development.level,
        "wage_type": resource,
        "employer_id": development.owner,
        "action_id": None,
    }


def _resolve_development_intents(game_state):
    for intent in list(game_state.phase_intents.values()):
        if isinstance(intent, MaintainIntent):
            _resolve_maintenance_intent(game_state, intent)
        elif isinstance(intent, UpgradeIntent):
            _resolve_upgrade_intent(game_state, intent)


def _resolve_maintenance_intent(game_state, intent):
    player = game_state.players.get(intent.player_id)
    development = game_state.developments.get(intent.development_id)
    if (
        not player
        or not development
        or development.owner != player.session_id
        or getattr(development, "is_contested", False)
    ):
        game_state.clear_intent(intent.player_id)
        return
    cost = development.get_maintenance_cost()
    if any(
        player.resources.get(resource, 0) < amount
        for resource, amount in cost.items()
    ):
        game_state.clear_intent(intent.player_id)
        return
    game_state.apply_events([
        PlayerResourcesSpent(player.session_id, cost.copy()),
        DevelopmentMaintained(development.id),
    ])
    player.add_timeline_event(
        "ACTION_COMPLETED",
        {"action": "MAINTAIN_DEV", "dev_id": development.id},
    )


def _resolve_upgrade_intent(game_state, intent):
    player = game_state.players.get(intent.player_id)
    development = game_state.developments.get(intent.development_id)
    if (
        not player
        or not development
        or development.owner != player.session_id
        or getattr(development, "is_contested", False)
        or not development.can_upgrade
    ):
        game_state.clear_intent(intent.player_id)
        return
    cost = development.get_upgrade_cost()
    if any(
        player.resources.get(resource, 0) < amount
        for resource, amount in cost.items()
    ):
        game_state.clear_intent(intent.player_id)
        return
    game_state.apply_events([
        PlayerResourcesSpent(player.session_id, cost.copy()),
        DevelopmentUpgraded(development.id),
    ])
    player.add_timeline_event(
        "ACTION_COMPLETED",
        {"action": "UPGRADE_DEV", "dev_id": development.id},
    )


def _resolve_upgrade_intents(game_state):
    for intent in list(game_state.phase_intents.values()):
        if not isinstance(intent, UpgradeIntent):
            continue
        _resolve_upgrade_intent(game_state, intent)


def _resolve_work_intents(game_state):
    for player in game_state.players.values():
        if player.health in ["sick", "recovering"]:
            continue
        intent = game_state.get_intent(player.session_id)
        if isinstance(intent, WorkIntent):
            development = game_state.developments.get(intent.development_id)
            if not development or getattr(development, "is_contested", False):
                continue
            committed_action = intent.job
            committed_action["development"] = development.to_dict()
        else:
            committed_action = getattr(player, "committed_action", None)
        if not committed_action or not isinstance(committed_action, dict):
            continue

        development = committed_action.get("development", {})
        owner_id = development.get("owner_id")
        development_type = development.get("type")
        development_level = int(development.get("level", 1))
        owner = game_state.players.get(owner_id)
        resource = DEVELOPMENT_OUTPUT.get(development_type)
        if not owner or not resource:
            continue

        game_state.apply_event(PlayerResourcesGained(
            owner.session_id,
            {resource: development_level},
        ))
        if owner_id != player.session_id:
            _create_wage_trade(
                game_state,
                employer=owner,
                worker=player,
                committed_action=committed_action,
            )
            owner.add_timeline_event(
                "LABOR_EXPLOITED",
                {
                    "worker": player.session_id,
                    "yield": development_level,
                    "type": resource,
                },
            )


def _create_wage_trade(game_state, employer, worker, committed_action):
    employment_id = committed_action.get("action_id")
    if not employment_id:
        return None

    employment = game_state.contract_factory.find_contract(employment_id)
    if (
        not employment
        or getattr(employment, "type", None) != "EMPLOYMENT"
        or getattr(employment, "status", None) != "ACCEPTED"
        or getattr(employment, "dev_id", None)
        != committed_action.get("development", {}).get("id")
    ):
        return None

    employment_employer_id = (
        employment.target_id
        if employment.is_application
        else employment.initiator_id
    )
    employment_worker_id = (
        employment.initiator_id
        if employment.is_application
        else employment.target_id
    )
    if (
        employment_employer_id != employer.session_id
        or employment_worker_id != worker.session_id
    ):
        return None

    existing = next((
        action
        for action in employer.actions.values()
        if getattr(action, "type", None) == "TRADE"
        and getattr(action, "employment_contract_id", None) == employment.id
    ), None)
    if existing:
        return existing

    wage_trade = TradeContract(
        employer.session_id,
        worker.session_id,
        {employment.wage_type: employment.wage},
        {},
        reason="WAGE_PAYMENT",
        employment_contract_id=employment.id,
        promised_wage={employment.wage_type: employment.wage},
    )
    wage_trade.status = "ACCEPTED"
    wage_trade.waiting_on_id = None
    game_state.apply_event(ContractCreated(wage_trade))
    return wage_trade


def start_work_phase(game_state):
    if game_state.status != "RUNNING":
        time.sleep(3)
        return

    for player in game_state.players.values():
        player.available_work = []

    for development in game_state.developments.values():
        if getattr(development, "is_contested", False):
            continue
        owner = game_state.players.get(development.owner)
        if not owner:
            continue

        resource = DEVELOPMENT_OUTPUT.get(development.type, "food")
        owner.available_work.append(
            {
                "development": (
                    development.to_dict()
                    if hasattr(development, "to_dict")
                    else development.__dict__
                ),
                "wage": development.level,
                "wage_type": resource,
                "employer_id": owner.session_id,
                "action_id": None,
            }
        )
