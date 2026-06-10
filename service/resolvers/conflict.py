class ConflictResolvers:

    @staticmethod
    def resolve_contests(game_state):

        for dev in game_state.developments.values():

            if not getattr(dev, 'is_contested', False):
                continue

            # -----------------------------------------------
            # Reset supporters
            # -----------------------------------------------

            dev.contester_supporters = []
            dev.owner_supporters = []

            # -----------------------------------------------
            # Tally support
            # -----------------------------------------------

            for player in game_state.players.values():

                ca = getattr(player, 'committed_action', None)

                if (
                    ca
                    and isinstance(ca, dict)
                    and ca.get('type') == 'CONTEST_ACTION'
                    and ca.get('dev_id') == dev.id
                ):

                    side = ca.get('side')

                    if side == 'CONTESTER':
                        dev.contester_supporters.append(player.session_id)

                    elif side == 'OWNER':
                        dev.owner_supporters.append(player.session_id)

            # -----------------------------------------------
            # Resolve
            # -----------------------------------------------

            contester_score = len(dev.contester_supporters)
            owner_score = len(dev.owner_supporters)

            contester_present = (
                dev.contest_initiator_id in dev.contester_supporters
            )

            owner_present = (
                dev.owner in dev.owner_supporters
            )

            # Attackers abandoned
            if not contester_present:

                dev.is_contested = False
                dev.contest_initiator_id = None

            # Owner absent -> attackers win
            elif not owner_present:

                dev.owner = dev.contest_initiator_id

                dev.is_contested = False
                dev.contest_initiator_id = None

            # Attackers outnumber defenders
            elif contester_score > owner_score:

                old_owner = game_state.players.get(dev.owner)
                new_owner = game_state.players.get(dev.contest_initiator_id)

                if old_owner and dev.id in old_owner.developments:
                    old_owner.developments.remove(dev.id)

                if new_owner and dev.id not in new_owner.developments:
                    new_owner.developments.append(dev.id)

                dev.owner = dev.contest_initiator_id
                dev.is_contested = False
                dev.contest_initiator_id = None

            # Defenders survive
            elif owner_score > contester_score:

                dev.is_contested = False
                dev.contest_initiator_id = None

            dev.contester_supporters = []
            dev.owner_supporters = []

# Put pending conflict logic here from game loop
