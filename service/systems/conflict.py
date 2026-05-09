class ConflictSystem:
    @staticmethod
    def action_contest_development(game_state, player, payload):
        """
        Handles initiating a new contest or joining an existing one.
        """
        if game_state.phase != 'WORK':
            return False

        dev_id = payload.get('dev_id')
        # side can be: 'INITIATOR', 'CONTESTER' (supporting), or 'OWNER' (defending)
        side = payload.get('side')

        dev = game_state.developments.get(dev_id)
        if not dev:
            return False

        # 1. Logic for Initiating a Brand New Contest
        if side == 'INITIATOR':
            if dev.is_contested:
                return False  # Already contested
            if dev.owner == player.session_id:
                return False  # Can't contest your own property

            # Apply the initial hold flag
            dev.contester_id = player.session_id

        # 2. Lock the action in for the Work Phase
        # We don't tally supporters yet; we do that at the end of the phase
        # so players can change their committed action before the timer ends.
        player.committed_action = {
            "type": "CONTEST_ACTION",
            "dev_id": dev_id,
            "side": 'CONTESTER' if side == 'INITIATOR' else side
        }

        player.add_timeline_event("ACTION_COMPLETED", {
            "action": "CONTEST",
            "dev_id": dev_id,
            "side": side
        })
        return True

    @staticmethod
    def resolve_contests(game_state):
        """
        Evaluates the stalemates, steals, and defenses at the end of the work phase.
        """
        # 1. First, process BRAND NEW initiations.
        # This flags them for tomorrow, but we skip the math today.
        for player in game_state.players.values():
            ca = getattr(player, 'committed_action', None)
            if ca and isinstance(ca, dict) and ca.get('type') == 'CONTEST_ACTION':
                if ca.get('side') == 'CONTESTER':
                    dev_id = ca.get('dev_id')
                    dev = game_state.developments.get(dev_id)

                    # If it wasn't contested yesterday, it is newly initiated today
                    if dev and not getattr(dev, 'is_contested', False):
                        dev.is_contested = True
                        dev.contester_id = player.session_id
                        # Tag it so we know to skip the math for it this turn
                        dev.just_initiated = True

        # 2. Reset the supporter tallies
        for dev in game_state.developments.values():
            if getattr(dev, 'is_contested', False):
                dev.contester_supporters = []
                dev.owner_supporters = []

        # 2. Tally up the committed actions from all players
        for player in game_state.players.values():
            ca = getattr(player, 'committed_action', None)
            if ca and isinstance(ca, dict) and ca.get('type') == 'CONTEST_ACTION':
                dev_id = ca.get('dev_id')
                dev = game_state.developments.get(dev_id)

                if dev and getattr(dev, 'is_contested', False):
                    side = ca.get('side')
                    if side == 'CONTESTER':
                        dev.contester_supporters.append(player.session_id)
                    elif side == 'OWNER':
                        dev.owner_supporters.append(player.session_id)

        # 3. Determine the outcome for each contested development
        for dev in game_state.developments.values():
            if not getattr(dev, 'is_contested', False):
                continue

            if getattr(dev, 'just_initiated', False):
                dev.just_initiated = False
                continue

            contester_score = len(dev.contester_supporters)
            owner_score = len(dev.owner_supporters)

            # Did the primary parties actually show up to the fight?
            contester_present = dev.contester_id in dev.contester_supporters
            owner_present = dev.owner in dev.owner_supporters

            # Condition A: The contester abandons the contest
            if not contester_present:
                dev.is_contested = False
                dev.contester_id = None

            # Condition B: The owner does not contest (defend) their property
            elif not owner_present:
                dev.owner = dev.contester_id
                dev.is_contested = False
                dev.contester_id = None

            # Condition C: Contester gets more players on their side -> Steal
            elif contester_score > owner_score:
                dev.owner = dev.contester_id
                dev.is_contested = False
                dev.contester_id = None

            # Condition D: Owner gets more players on their side -> Defense succeeds
            elif owner_score > contester_score:
                dev.is_contested = False
                dev.contester_id = None

            # Condition E: Scores are equal -> Stalemate continues to the next phase
            else:
                pass  # Flags remain untouched, trapping them in the stalemate

            # Clean up the support arrays for the next day's memory
            dev.contester_supporters = []
            dev.owner_supporters = []
