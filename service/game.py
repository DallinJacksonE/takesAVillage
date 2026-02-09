import time
import random
from models.player import Player
from models.message import MessageFactory
from models.map import MapFactory
from models.developments import Development
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

        current_amount = self.work_phase_resources[owner_id].get(
            res_type, 0)
        self.work_phase_resources[owner_id][res_type] = current_amount + quantity

        return self.action_finish_phase(player)

    def action_finish_phase(self, player):
        player.finished_phase = True
        self.check_all_players_locked()
        return True

    def action_build_development(self, player, payload):
        tile_id = payload.get('tile_id')
        tile = next((t for t in self.map_tiles if t['id'] == tile_id), None)
        if not tile or tile['owner_id'] is not None:
            return False

        cost_wood = 2
        if player.resources['wood'] < cost_wood:
            return False

        player.resources['wood'] -= cost_wood
        tile['owner_id'] = player.session_id
        tile['level'] = 2
        new_dev = Development(tile['id'], tile['type'], player.session_id)
        new_dev.level = 2
        self.developments[new_dev.id] = new_dev
        player.developments.append(new_dev.id)

        return self.action_finish_phase(player)

    # --- Unified Message Handling ---

    def handle_message_action(self, user_id, data):
        """
        Handles creation AND updates of messages.
        Checks for game side-effects (like auto-working upon accepting a job).
        """
        status, msg = self.message_factory.process_message(user_id, data)

        if status == "ACCEPTED_EMPLOYMENT" and self.phase == "WORK":
            # Auto-execute the work action for the employee
            player = self.players.get(user_id)
            if player:
                self.action_work_development(player, {'dev_id': msg.dev_id})
                self.check_all_players_locked()

        return status in ["CREATED", "UPDATED", "ACCEPTED_EMPLOYMENT"]

    # --- Phase Resolution ---

    def resolve_work_phase(self):
        for pid, resources in self.work_phase_resources.items():
            player = self.players.get(pid)
            if player:
                for res_type, amount in resources.items():
                    player.resources[res_type] = player.resources.get(
                        res_type, 0) + amount
        self.work_phase_resources = {}

        for player in self.players.values():
            for msg in player.messages.values():
                if msg.type == 'EMPLOYMENT' and msg.status == 'ACCEPTED':
                    # Execute wages using factory's update mechanism
                    self.message_factory.process_message(
                        msg.from_id, {'id': msg.id, 'action': 'EXECUTE'})

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
            tile = next((t for t in self.map_tiles if t['id'] == dev.id), None)
            if tile:
                tile['level'] = dev.level

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

        my_devs_full = []
        for dev_id in me.developments:
            dev_obj = self.developments.get(dev_id)
            if dev_obj:
                my_devs_full.append(vars(dev_obj))

        my_data = me.to_dict()
        my_data['developments'] = my_devs_full

        other_players = [
            {"id": pid, "name": p.name}
            for pid, p in self.players.items()
            if pid != session_id
        ]

        return {
            "game_id": self.game_id,
            "status": self.state,
            "session_id": session_id,
            "day": self.day,
            "phase": self.phase,
            "time_remaining": int(self.phase_end_time - time.time()) if self.state == 'RUNNING' else 0,
            "me": my_data,
            "map": self.map_tiles,
            "messages": my_data['messages'],
            "player_count": len(self.players),
            "player_list": other_players,
            "is_host": session_id == self.host_id
        }
