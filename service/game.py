import time
import random
from models.player import Player
from models.message import MessageFactory
from models.map import MapFactory
from models.developments import Development
from dtos import PlayerDTO, GameStateDTO, MapTileDTO, message_dto_factory
from itertools import count


class Game:
    def __init__(self, game_id, host_id):
        self.game_id = game_id
        self.host_id = host_id
        self.players = {}
        self.map_tiles = []
        self.name_gen = self.name_generator()
        self.state = "WAITING"
        self.day = 1
        self.phase = "WORK"
        self.developments = {}
        self.work_phase_resources = {}
        self.phase_duration = 180
        self.phase_end_time = 0
        self.active_conflicts = {}

    def add_player(self, session_id):
        if self.state == "WAITING" and session_id not in self.players:
            name = next(self.name_gen)
            self.players[session_id] = Player(session_id, name)
            return True
        return False

    def start_game(self):
        if len(self.players) > 1:
            self.state = "RUNNING"
            self.message_factory = MessageFactory(self.players)
            self.map_factory = MapFactory(len(self.players))
            self.map_tiles = self.map_factory.map_tiles
            self.start_phase("WORK")
            return True
        return False

    def start_phase(self, phase_name):
        self.phase = phase_name
        self.phase_end_time = time.time() + self.phase_duration
        for p in self.players.values():
            p.finished_phase = False
            if phase_name == "NIGHT":
                p.current_fire_host = None
        if phase_name == "TRADE":
            self.generate_payout_messages()

    def check_timer(self):
        if self.state == "RUNNING" and time.time() > self.phase_end_time:
            self.next_phase()
            return True
        return False

    def next_phase(self):
        if self.phase == "WORK":
            self.resolve_work_phase()
            self.start_phase("TRADE")
        elif self.phase == "TRADE":
            self.resolve_trade_phase()
            self.start_phase("NIGHT")
        elif self.phase == "NIGHT":
            self.resolve_night_phase()
            self.day += 1
            self.start_phase("WORK")

    def handle_user_action(self, user_id, action, payload):
        player = self.players.get(user_id)
        if not player:
            return False
        if player.finished_phase and action != 'FINISH_PHASE':
            return False

        if action == 'BUILD_DEV':
            return self.action_build_development(player, payload)
        if action == 'WORK_DEV':
            return self.action_work_development(player, payload)
        if action == 'FINISH_PHASE':
            return self.action_finish_phase(player)
        return False

    def action_work_development(self, player, payload):
        dev_id = payload.get('dev_id')

        dev = self.developments.get(dev_id)
        if not dev:
            return False

        owner_id = dev.owner

        res_map = {'Farm': 'food', 'Woods': 'wood', 'Mine': 'iron'}
        res_type = res_map.get(dev.type)
        if not res_type:
            return False

        quantity = 1 * dev.level

        if owner_id not in self.work_phase_resources:
            self.work_phase_resources[owner_id] = {}

        current_amount = self.work_phase_resources[owner_id].get(res_type, 0)
        self.work_phase_resources[owner_id][res_type] = (
            current_amount + quantity
        )

        return self.action_finish_phase(player)

    def action_finish_phase(self, player):
        player.finished_phase = True
        self.check_all_players_locked()
        return True

    def action_build_development(self, player, payload):
        tile_id = payload.get('tile_id')

        tile = next((t for t in self.map_tiles if t.id == tile_id), None)
        if not tile or tile.owner_id is not None:
            return False

        cost_wood = 2
        if player.resources['wood'] < cost_wood:
            return False

        player.resources['wood'] -= cost_wood
        tile.owner_id = player.session_id

        new_dev = Development(tile.id, tile.type, player.session_id)
        new_dev.level = 2
        self.developments[new_dev.id] = new_dev
        player.developments.append(new_dev.id)

        return self.action_finish_phase(player)

    # --- Unified Message Handling ---

    def handle_message_action(self, user_id, data):
        status, msg = self.message_factory.process_message(user_id, data)

        if not msg:
            return False

        if status == "ACCEPTED_EMPLOYMENT" and self.phase == "WORK":
            employee_id = getattr(msg, 'to_id', None)
            player = self.players.get(employee_id) if employee_id else None

            if player:
                self.action_work_development(
                    player, {'dev_id': getattr(msg, 'dev_id', None)}
                )
                self.check_all_players_locked()

        elif status == "TRADE_COMPLETED":
            from_id = getattr(msg, 'from_id', None)
            to_id = getattr(msg, 'to_id', None)

            sender = self.players.get(from_id) if from_id else None
            recipient = self.players.get(to_id) if to_id else None

            if sender and recipient:
                offer_items = getattr(
                    msg, 'actual_offer_items', getattr(msg, 'offer_items', {})
                )
                for res, amt in offer_items.items():
                    actual_amt = min(amt, sender.resources.get(res, 0))
                    sender.resources[res] = (
                        sender.resources.get(res, 0) - actual_amt
                    )
                    recipient.resources[res] = (
                        recipient.resources.get(res, 0) + actual_amt
                    )

                req_items = getattr(
                    msg, 'actual_request_items', getattr(
                        msg, 'request_items', {})
                )
                for res, amt in req_items.items():
                    actual_amt = min(amt, recipient.resources.get(res, 0))
                    recipient.resources[res] = (
                        recipient.resources.get(res, 0) - actual_amt
                    )
                    sender.resources[res] = (
                        sender.resources.get(res, 0) + actual_amt
                    )

        valid_statuses = [
            "CREATED", "UPDATED", "ACCEPTED_EMPLOYMENT",
            "BARTER", "TRADE_COMPLETED"
        ]
        return status in valid_statuses

    # --- Phase Resolution ---

    def resolve_work_phase(self):
        for pid, resources in self.work_phase_resources.items():
            player = self.players.get(pid)
            if player:
                for res_type, amount in resources.items():
                    player.resources[res_type] = (
                        player.resources.get(res_type, 0) + amount
                    )
        self.work_phase_resources = {}

        for player in self.players.values():
            for msg in player.messages.values():
                if msg.type == 'EMPLOYMENT' and msg.status == 'ACCEPTED':
                    self.message_factory.process_message(
                        msg.from_id, {'id': msg.id, 'action': 'EXECUTE'}
                    )

        for p in self.players.values():
            p.reset_phase()

    def resolve_trade_phase(self):
        for p in self.players.values():
            p.reset_phase()

    def resolve_night_phase(self):
        for p in self.players.values():
            p.consume_daily()
            p.reset_phase()

        for dev in self.developments.values():
            dev.degrade()

    def check_all_players_locked(self):
        if all(p.finished_phase for p in self.players.values()):
            self.next_phase()

    def generate_payout_messages(self):
        pass

    def name_generator(self, filename='names/goblinNames.txt'):
        try:
            with open(filename, 'r') as f:
                pool = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return
        random.shuffle(pool)
        yield from pool
        for i in count(1):
            yield f"Settler {i}"

    def get_state_for_player(self, session_id):
        me = self.players.get(session_id)
        if not me:
            return None

        my_devs_full = [
            self.developments[d]
            for d in me.developments if d in self.developments
        ]
        me_dto = PlayerDTO.from_model(me, my_devs_full)

        player_list_dtos = []
        for pid, p in self.players.items():
            if pid != session_id:
                their_devs = [
                    self.developments[d]
                    for d in p.developments if d in self.developments
                ]
                player_list_dtos.append(PlayerDTO.from_model(p, their_devs))

        map_dtos = [
            MapTileDTO(
                id=t.id, q=t.q, r=t.r, type=t.type, owner_id=t.owner_id
            )
            for t in self.map_tiles
        ]
        messages_dtos = [message_dto_factory(m) for m in me.messages.values()]

        is_running = self.state == 'RUNNING'

        game_state = GameStateDTO(
            status=self.state,
            is_host=session_id == self.host_id,
            me=me_dto,
            day=self.day,
            phase=self.phase,
            time_remaining=(
                int(self.phase_end_time - time.time()) if is_running else 0
            ),
            player_list=player_list_dtos,
            map=map_dtos,
            messages=messages_dtos,
            session_id=session_id
        )

        return game_state.to_dict()
