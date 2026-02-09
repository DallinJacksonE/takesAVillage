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

        # Game State
        self.state = "WAITING"
        self.day = 1
        self.phase = "WORK"

        # Stores Development Objects: { "dev_uuid": DevelopmentObj }
        self.developments = {}

        # Pending production: { player_id: { "food": 5, "wood": 2 } }
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

        # Reset Phase specific flags
        for p in self.players.values():
            p.finished_phase = False  # Unlock players for new phase
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

    # --- User Action Handling ---

    def handle_user_action(self, user_id, action, payload):
        player = self.players.get(user_id)
        if not player:
            return False

        # If player has already clicked "Finish Phase", block actions
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
        """
        Calculates production based on Dev Level and Type.
        Stores it in a temporary buffer until phase resolution.
        """
        dev_id = payload.get('dev_id')

        # Ensure player owns or has rights to this dev
        # (Simplified: currently only owners can work their devs in this logic,
        # unless you want to add 'delegated' work logic here)
        if dev_id not in player.available_work:
            return False

        dev = self.developments.get(dev_id)
        if not dev:
            return False

        # Determine Resource Type
        res_map = {'Farm': 'food', 'Woods': 'wood', 'Mine': 'iron'}
        res_type = res_map.get(dev.type)
        if not res_type:
            return False

        # Calculate Quantity (Base 2 * Level)
        quantity = 2 * dev.level

        # Initialize buffer if empty
        if player.session_id not in self.work_phase_resources:
            self.work_phase_resources[player.session_id] = {}

        # Add to buffer
        current_amount = self.work_phase_resources[player.session_id].get(
            res_type, 0)
        self.work_phase_resources[player.session_id][res_type] = current_amount + quantity

        # Lock player
        return self.action_finish_phase(player)

    def action_finish_phase(self, player):
        player.finished_phase = True
        self.check_all_players_locked()
        return True

    def action_build_development(self, player, payload):
        tile_id = payload.get('tile_id')

        # 1. Find the tile
        tile = next((t for t in self.map_tiles if t['id'] == tile_id), None)
        if not tile:
            return False

        # 2. Validation
        if tile['owner_id'] is not None:
            return False

        cost_wood = 2
        if player.resources['wood'] < cost_wood:
            return False

        # 3. Execution
        player.resources['wood'] -= cost_wood

        # Update Map Tile
        tile['owner_id'] = player.session_id
        # Starts at level 1 usually? (Changed from 2 in your original)
        tile['level'] = 1

        # Create Development Object
        # Note: Tile type 'Farm' -> Dev type 'Farm'
        new_dev = Development(tile['id'], tile['type'], player.session_id)
        new_dev.level = 1  # Explicitly set start level

        # Store in Game Registry
        self.developments[new_dev.id] = new_dev

        # Store ID in Player
        player.developments.append(new_dev.id)

        return True

    # --- Message Handling ---

    def create_message(self, from_id, data):
        success, msg = self.message_factory.create_message(data)
        return success

    def handle_message_update(self, user_id, msg_id, action, values=None):
        updated = self.message_factory.update_msg(
            msg_id=msg_id,
            user_id=user_id,
            action=action,
            values=values,
            game_phase=self.phase
        )

        if updated:
            if action == 'ACCEPT' and self.phase == 'WORK':
                self.check_all_players_locked()
            return True
        return False

    # --- Phase Resolution Logic ---

    def resolve_work_phase(self):
        """
        1. Grant generated resources to producers.
        2. Process payments for Employment contracts.
        """
        # 1. Distribute Production
        for pid, resources in self.work_phase_resources.items():
            player = self.players.get(pid)
            if player:
                for res_type, amount in resources.items():
                    player.resources[res_type] = player.resources.get(
                        res_type, 0) + amount

        # Clear the production buffer
        self.work_phase_resources = {}

        # 2. Process Wages (Employment)
        # Scan all players for ACCEPTED employment messages
        for player in self.players.values():
            for msg in player.messages.values():
                if msg.type == 'EMPLOYMENT' and msg.status == 'ACCEPTED':
                    # Execute the transaction
                    # Note: We rely on the MessageFactory execution logic
                    # We spoof the 'EXECUTE' action to trigger the money transfer
                    self.message_factory.update_msg(
                        msg_id=msg.id,
                        user_id=msg.from_id,  # Owner triggers it effectively
                        action='EXECUTE'
                    )

        # Reset for next phase
        for p in self.players.values():
            p.reset_phase()

    def resolve_trade_phase(self):
        """
        Finalize any trades that are stuck or auto-expire offers.
        """
        # In this simplified version, we just clear player locks.
        # Complex logic: Could auto-deny pending trades here.
        for p in self.players.values():
            p.reset_phase()

    def resolve_night_phase(self):
        """
        1. Players consume food/wood.
        2. Developments degrade (maintenance).
        """
        # 1. Player Survival
        for p in self.players.values():
            p.consume_daily()
            p.reset_phase()

        # 2. Building Maintenance
        # Use a list to avoid runtime errors if we need to remove devs (optional)
        for dev in self.developments.values():
            dev.degrade()
            # If you want to reflect level changes back to the map tiles:
            tile = next((t for t in self.map_tiles if t['id'] == dev.id), None)
            if tile:
                tile['level'] = dev.level

    # --- Helpers ---

    def check_all_players_locked(self):
        # Optimization: Don't force next phase if it's barely started
        if all(p.finished_phase for p in self.players.values()):
            self.next_phase()

    def generate_payout_messages(self):
        # Placeholder if specific notification messages are needed
        pass

    def name_generator(self, filename='names/goblinNames.txt'):
        try:
            with open(filename, 'r') as f:
                pool = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print("FileNotFoundError")
            return
        random.shuffle(pool)
        yield from pool

        for i in count(1):
            yield f"Settler {i}"

    def get_state_for_player(self, session_id):
        me = self.players.get(session_id)
        if not me:
            return None

        # Convert Dev Objects to dicts for the UI
        my_devs_full = []
        for dev_id in me.developments:
            dev_obj = self.developments.get(dev_id)
            if dev_obj:
                my_devs_full.append(vars(dev_obj))  # Simple obj to dict

        # Update the 'me' dict with full development info
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
