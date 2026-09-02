from service.game.packet_handling.base import Command
from service.game.state.events import (
    DevelopmentContestActivated,
    DevelopmentContestCleared,
    DevelopmentOwnershipTransferred,
)
from service.game.state.intents import ContestIntent
from service.game.state.developments import has_active_contest_initiation


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
                player.finished_phase
                or development.is_contested
                or development.owner == player.session_id
                or has_active_contest_initiation(
                    game_state.developments, player.session_id)
            ):
                return False
            game_state.apply_event(DevelopmentContestActivated(
                development.id,
                player.session_id,
            ))
            game_state.invalidate_intents_for_development(
                development.id, "development_contested")
            game_state.extend_phase_timer_for_contest()
            game_state.notify_village({
                "level": "warning",
                "reason": "development_contested",
                "message": "A village development is now under contest.",
                "development_id": development.id,
            })
            player.add_timeline_event(
                "ACTION_COMPLETED",
                {"action": "CONTEST_STARTED", "dev_id": dev_id},
            )
            game_state.set_intent(
                ContestIntent(player.session_id, dev_id, "CONTESTER")
            )
            return True

        if side == "CONTESTER":
            if not development.is_contested:
                return False
        elif side == "OWNER":
            if not development.is_contested:
                return False
        else:
            return False

        game_state.set_intent(
            ContestIntent(player.session_id, dev_id, side)
        )
        player.add_timeline_event(
            "ACTION_INTENT_SUBMITTED",
            {"action": "CONTEST", "dev_id": dev_id, "side": side},
        )
        return True


def activate_pending_contests(game_state):
    for development in game_state.developments.values():
        if (
            getattr(development, "pending_contest", False)
            and development.pending_contest_day == game_state.day
        ):
            game_state.apply_event(DevelopmentContestActivated(
                development.id,
                development.contest_initiator_id,
            ))
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
        for intent in game_state.phase_intents.values():
            if not isinstance(intent, ContestIntent):
                continue
            if intent.development_id != development.id:
                continue
            if intent.side == "CONTESTER":
                development.contester_supporters.append(intent.player_id)
            elif intent.side == "OWNER":
                development.owner_supporters.append(intent.player_id)

        contester_score = len(development.contester_supporters)
        owner_score = len(development.owner_supporters)
        contester_present = (
            development.contest_initiator_id
            in development.contester_supporters
        )
        owner_present = development.owner in development.owner_supporters

        if not contester_present:
            game_state.apply_event(DevelopmentContestCleared(development.id))
        elif not owner_present or contester_score > owner_score:
            game_state.apply_events([
                DevelopmentOwnershipTransferred(
                    development.id,
                    development.owner,
                    development.contest_initiator_id,
                ),
                DevelopmentContestCleared(development.id),
            ])
        elif owner_score > contester_score:
            game_state.apply_event(DevelopmentContestCleared(development.id))
        else:
            # Ties remain active into the next work phase.
            development.contester_supporters = []
            development.owner_supporters = []
