"""Player-facing legal action projection.

This is intentionally conservative: it exposes commands that the current
phase/player state can consider, while command handlers remain the final guard.
"""

from service.game.packet_handling.dispatcher import PacketDispatcher


MAIN_PHASE_COMMANDS = {
    "BUILD_DEV",
    "MAINTAIN_DEV",
    "UPGRADE_DEV",
    "COMMIT_WORK",
    "START_FIRE",
}


def get_legal_actions(game, player_id):
    player = game.players.get(player_id)
    if not player or player.health == "dead":
        return []

    actions = []
    _add(actions, "FINISH_PHASE", {})

    for contract in getattr(player, "actions", {}).values():
        _add_contract_actions(actions, contract, player_id)

    if player.finished_phase:
        _add_contest_responses(game, player_id, actions, include_initiation=False)
        return actions

    if game.phase == "WORK":
        _add_work_actions(game, player, actions)
    elif game.phase == "NIGHT":
        if getattr(player, "fire_status", "COLD") == "COLD":
            _add(actions, "START_FIRE", {})

    _add_contest_responses(game, player_id, actions)
    return [
        action for action in actions
        if PacketDispatcher.player_can_perform_action(
            game, player, action["action_command"])
    ]


def _add_work_actions(game, player, actions):
    if getattr(player, "available_work", []):
        for job in player.available_work:
            development = job.get("development", {})
            if development.get("id"):
                _add(actions, "COMMIT_WORK", {"job": job})

    owned_developments = [
        development for development in game.developments.values()
        if development.owner == player.session_id
    ]
    if owned_developments:
        for development in owned_developments:
            _add(actions, "MAINTAIN_DEV", {"dev_id": development.id})
            if development.can_upgrade:
                _add(actions, "UPGRADE_DEV", {"dev_id": development.id})

    buildable_tiles = [
        tile for tile in game.map_data.values()
        if getattr(tile, "development", None) is None
        and getattr(tile, "type", None) in game.development_costs
    ]
    if buildable_tiles:
        _add(actions, "BUILD_DEV", {"tile_id": buildable_tiles[0].id})


def _add_contest_responses(
        game, player_id, actions, include_initiation=True):
    for development in game.developments.values():
        if getattr(development, "is_contested", False):
            side = (
                "OWNER" if development.owner == player_id else "CONTESTER"
            )
            _add(actions, "CONTEST_DEV", {
                "dev_id": development.id,
                "side": side,
            })
        elif include_initiation and development.owner != player_id:
            _add(actions, "CONTEST_DEV", {
                "dev_id": development.id,
                "side": "INITIATOR",
            })


def _add_contract_actions(actions, contract, player_id):
    status = getattr(contract, "status", None)
    if status == "PENDING" and getattr(contract, "waiting_on_id", None) == player_id:
        _add(actions, "ACCEPT", {"action_id": contract.id})
        _add(actions, "DENY", {"action_id": contract.id})
        if getattr(contract, "type", None) == "TRADE":
            _add(actions, "BARTER", {"action_id": contract.id})
    if status == "PENDING" and getattr(contract, "initiator_id", None) == player_id:
        _add(actions, "CANCEL", {"action_id": contract.id})
    if status == "ACCEPTED" and getattr(contract, "type", None) == "TRADE":
        _add(actions, "FINALIZE", {"action_id": contract.id})


def _add(actions, action_command, payload):
    actions.append({
        "action_command": action_command,
        "payload": payload,
    })
