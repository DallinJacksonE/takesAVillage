from service.game.actions.base import Command


class ContestDevelopmentCommand(Command):
    def execute(self, game_state, player):
        if game_state.phase != "WORK":
            return False
        if player.health in ["sick", "recovering"]:
            return False

        dev_id = self.payload.get("dev_id")
        side = self.payload.get("side")
        development = game_state.developments.get(dev_id)
        if not development:
            return False

        if side == "INITIATOR":
            if (
                development.is_contested
                or development.pending_contest
                or development.owner == player.session_id
            ):
                return False
            development.pending_contest = True
            development.contest_initiator_id = player.session_id
            development.pending_contest_day = game_state.day + 1
            player.add_timeline_event(
                "ACTION_COMPLETED",
                {"action": "CONTEST_SCHEDULED", "dev_id": dev_id},
            )
            game_state.contest_count += 1
            return True

        if side == "CONTESTER":
            if not development.is_contested:
                return False
            if player.session_id not in development.contester_supporters:
                development.contester_supporters.append(player.session_id)
        elif side == "OWNER":
            if not development.is_contested:
                return False
            if player.session_id not in development.owner_supporters:
                development.owner_supporters.append(player.session_id)

        player.committed_action = {
            "type": "CONTEST_ACTION",
            "dev_id": dev_id,
            "side": side,
        }
        player.add_timeline_event(
            "ACTION_COMPLETED",
            {"action": "CONTEST", "dev_id": dev_id, "side": side},
        )
        return True


def activate_pending_contests(game_state):
    for development in game_state.developments.values():
        if (
            getattr(development, "pending_contest", False)
            and development.pending_contest_day == game_state.day
        ):
            development.is_contested = True
            development.contester_supporters = []
            development.pending_contest = False
            owner = game_state.players.get(development.owner)
            if owner:
                owner.add_timeline_event(
                    "CONTEST_STARTED",
                    {
                        "dev_id": development.id,
                        "attacker": development.contest_initiator_id,
                    },
                )


def resolve_contests(game_state):
    for development in game_state.developments.values():
        if not getattr(development, "is_contested", False):
            continue

        development.contester_supporters = []
        development.owner_supporters = []
        for player in game_state.players.values():
            action = getattr(player, "committed_action", None)
            if (
                action
                and isinstance(action, dict)
                and action.get("type") == "CONTEST_ACTION"
                and action.get("dev_id") == development.id
            ):
                side = action.get("side")
                if side == "CONTESTER":
                    development.contester_supporters.append(
                        player.session_id
                    )
                elif side == "OWNER":
                    development.owner_supporters.append(player.session_id)

        contester_score = len(development.contester_supporters)
        owner_score = len(development.owner_supporters)
        contester_present = (
            development.contest_initiator_id
            in development.contester_supporters
        )
        owner_present = development.owner in development.owner_supporters

        if not contester_present:
            development.is_contested = False
            development.contest_initiator_id = None
        elif not owner_present or contester_score > owner_score:
            old_owner = game_state.players.get(development.owner)
            new_owner = game_state.players.get(
                development.contest_initiator_id
            )
            if old_owner and development.id in old_owner.developments:
                old_owner.developments.remove(development.id)
            if new_owner and development.id not in new_owner.developments:
                new_owner.developments.append(development.id)
            development.owner = development.contest_initiator_id
            development.is_contested = False
            development.contest_initiator_id = None
        elif owner_score > contester_score:
            development.is_contested = False
            development.contest_initiator_id = None

        development.contester_supporters = []
        development.owner_supporters = []
