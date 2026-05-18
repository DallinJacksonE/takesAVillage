class ConflictResolvers:
    @staticmethod
    def resolve_contests(game_state):
        # 1. Flag new initiations
        for player in game_state.players.values():
            ca = getattr(player, 'committed_action', None)
            if ca and isinstance(ca, dict) and ca.get('type') == 'CONTEST_ACTION':
                if ca.get('side') == 'CONTESTER':
                    dev_id = ca.get('dev_id')
                    dev = game_state.developments.get(dev_id)
                    if dev and not getattr(dev, 'is_contested', False):
                        dev.is_contested = True
                        dev.contest_initiator_id = player.session_id
                        dev.just_initiated = True

        # 2. Reset supporters
        for dev in game_state.developments.values():
            if getattr(dev, 'is_contested', False):
                dev.contester_supporters = []
                dev.owner_supporters = []

        # 3. Tally support
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

        # 4. Determine outcomes
        for dev in game_state.developments.values():
            if not getattr(dev, 'is_contested', False):
                continue
            if getattr(dev, 'just_initiated', False):
                dev.just_initiated = False
                continue

            contester_score = len(dev.contester_supporters)
            owner_score = len(dev.owner_supporters)
            contester_present = dev.contest_initiator_id in dev.contester_supporters
            owner_present = dev.owner in dev.owner_supporters

            if not contester_present:
                dev.is_contested = False
                dev.contest_initiator_id = None
            elif not owner_present:
                dev.owner = dev.contest_initiator_id
                dev.is_contested = False
                dev.contest_initiator_id = None
            elif contester_score > owner_score:
                dev.owner = dev.contest_initiator_id
                dev.is_contested = False
                dev.contester_id = None
            elif owner_score > contester_score:
                dev.is_contested = False
                dev.contest_initiator_id = None

            dev.contester_supporters = []
            dev.owner_supporters = []
