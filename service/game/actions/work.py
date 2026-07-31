import time

from service.game.actions.base import Command
from service.game.actions.contracts import TradeContract


DEVELOPMENT_OUTPUT = {"Farm": "food", "Woods": "wood", "Mine": "iron"}


class CommitWorkCommand(Command):
    def execute(self, game_state, player):
        if player.health in ["sick", "recovering", "dead"]:
            return False

        job_data = self.payload.get("job")
        if not job_data:
            return False

        action_id = job_data.get("action_id")
        dev_id = job_data.get("development", {}).get("id")
        live_dev = game_state.developments.get(dev_id)
        if live_dev and getattr(live_dev, "is_contested", False):
            return False

        if action_id:
            chosen_action = game_state.contract_factory.find_contract(
                action_id
            )
            if chosen_action:
                chosen_action.status = "COMPLETED"
                if chosen_action.type == "EMPLOYMENT":
                    wage_trade = TradeContract(
                        initiator_id=chosen_action.target_id,
                        target_id=chosen_action.initiator_id,
                        offer_items={
                            chosen_action.wage_type: chosen_action.wage
                        },
                        request_items={},
                    )
                    wage_trade.status = "ACCEPTED"
                    wage_trade.target_finalized = True
                    game_state.contract_factory._add_contract_to_players(
                        wage_trade
                    )

                for action in list(player.actions.values()):
                    if (
                        getattr(action, "type", None) == "EMPLOYMENT"
                        and action.status == "ACCEPTED"
                        and action.id != action_id
                    ):
                        action.status = "CANCELED"

        player.committed_action = job_data
        return True


def resolve_work_phase(game_state):
    for player in game_state.players.values():
        if player.health in ["sick", "recovering"]:
            continue
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

        owner.resources[resource] = (
            owner.resources.get(resource, 0) + development_level
        )
        if owner_id != player.session_id:
            owner.add_timeline_event(
                "LABOR_EXPLOITED",
                {
                    "worker": player.session_id,
                    "yield": development_level,
                    "type": resource,
                },
            )


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
