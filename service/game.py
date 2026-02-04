import time
import random
from models.player import Player
from models.message import TextMessage, EmploymentOffer, TradeOffer, FireOffer
from itertools import count


class Game:
    def __init__(self, game_id, host_id):
        self.game_id = game_id
        self.host_id = host_id
        self.players = {}
        self.messages = []
        self.map_tiles = []
        self.name_gen = self.name_generator()

        # Game State
        self.state = "WAITING"
        self.day = 1
        self.phase = "WORK"

        # Timer Logic
        self.phase_duration = 180  # 3 minutes
        self.phase_end_time = 0

        # Conflict Logic
        self.active_conflicts = {}

    def add_player(self, session_id):
        if self.state == "WAITING" and session_id not in self.players:
            name = next(self.name_gen)
            self.players[session_id] = Player(session_id, name)
            return True
        return False

    def start_game(self):
        if len(self.players) > 1:
            self.generate_map()
            self.state = "RUNNING"
            self.start_phase("WORK")
            return True
        return False

    def start_phase(self, phase_name):
        self.phase = phase_name
        self.phase_end_time = time.time() + self.phase_duration

        # Reset daily flags for players
        for p in self.players.values():
            if phase_name == "WORK":
                p.action_locked = False
            elif phase_name == "NIGHT":
                p.current_fire_host = None

        # Phase Specific Setup
        if phase_name == "TRADE":
            self.generate_payout_messages()

        # Clean up old messages from previous phases
        self.cleanup_messages()

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

    # --- Message Handling ---

    def create_message(self, from_id, data):
        """
        Factory to create messages based on type.
        data = {to_id, type, details...}
        """
        to_id = data.get('to_id')
        msg_type = data.get('type')

        new_msg = None

        if msg_type == 'TEXT':
            new_msg = TextMessage(from_id, to_id, data.get('content', ''))

        elif msg_type == 'EMPLOYMENT':
            # wage_offer, wage_type, dev_id
            new_msg = EmploymentOffer(
                from_id, to_id,
                data.get('dev_id'),
                data.get('wage_offer'),
                data.get('wage_type')
            )

        elif msg_type == 'TRADE':
            # offer_items, request_items
            new_msg = TradeOffer(
                from_id, to_id,
                data.get('offer_items', {}),
                data.get('request_items', {})
            )

        elif msg_type == 'FIRE':
            # action: 'INVITE' or 'REQUEST'
            new_msg = FireOffer(from_id, to_id, data.get('action'))

        if new_msg:
            self.messages.insert(0, new_msg)  # Add to top
            return True
        return False

    def handle_message_update(self, user_id, msg_id, action, values=None):
        """
        Handles ACCEPT, DENY, BARTER, and 'PAYOUT' updates.
        """
        # Find message
        msg = next((m for m in self.messages if m.id == msg_id), None)
        if not msg:
            return False

        # 1. Barter / Update Values
        if action == 'BARTER':
            # Only allow bartering if pending or already bartering
            if msg.status not in ['PENDING', 'BARTERING']:
                return False

            msg.update(values)
            msg.status = 'BARTERING'
            return True

        # 2. Deny
        if action == 'DENY':
            msg.status = 'DENIED'
            return True

        # 3. Accept
        if action == 'ACCEPT':
            # WORK PHASE: Employment
            if self.phase == 'WORK' and msg.type == 'EMPLOYMENT':
                msg.status = 'ACCEPTED'

                # Lock the employee's action
                # Logic: If I am the one accepting the job, I am the employee
                # Or if I sent the request and they accepted...
                # Simplification: The person receiving the wage is the employee.

                # If this was an offer (From Employer -> To Employee)
                # Then 'to_id' is the employee.
                employee_id = msg.to_id
                self.players[employee_id].action_locked = True

                # Check if everyone is locked to auto-advance
                self.check_all_players_locked()
                return True

            # TRADE PHASE: Trade Offers
            if self.phase == 'TRADE' and msg.type == 'TRADE':
                msg.status = 'ACCEPTED'
                # Transition to "Green Border" state where lying is possible
                # Actual exchange happens when they click "CONFIRM" or Phase Ends
                return True

            # FIRE SHARING
            if self.phase == 'NIGHT' and msg.type == 'FIRE':
                msg.status = 'ACCEPTED'
                # If Invite: To_ID gets fire. If Request: From_ID gets fire.
                beneficiary = msg.to_id if msg.action == 'INVITE' else msg.from_id
                provider = msg.from_id if msg.action == 'INVITE' else msg.to_id

                # Logic: Provider loses 1 wood immediately? Or at end of night?
                # Prompt: "Player can promise to share... message board used... automatic consumption"
                self.players[beneficiary].current_fire_host = provider
                return True

        # 4. Special: Update Actual Payload (Lying)
        if action == 'UPDATE_PAYLOAD':
            if msg.from_id != user_id:
                return False  # Only sender can change their payload

            if hasattr(msg, 'actual_payout'):  # Employment Payout
                msg.actual_payout = int(values.get('wage_offer', 0))
                msg.actual_payout_type = values.get('wage_type', 'food')

            elif hasattr(msg, 'actual_offer_items'):  # Trade Offer
                msg.actual_offer_items = values.get('offer_items', {})

            return True

        # 5. Special: Execute Transaction (Pay Employee / Finish Trade)
        if action == 'EXECUTE':
            if msg.type == 'EMPLOYMENT' and msg.status == 'ACCEPTED':
                # Payout logic
                employer = self.players[msg.from_id]
                employee = self.players[msg.to_id]

                amt = msg.actual_payout
                res = msg.actual_payout_type

                if employer.resources.get(res, 0) >= amt:
                    employer.resources[res] -= amt
                    employee.resources[res] += amt
                    msg.status = 'COMPLETED'
                return True

            if msg.type == 'TRADE' and msg.status == 'ACCEPTED':
                # Determine who is 'executing'.
                # For simplicity, trades might auto-execute or require a final button.
                pass

        return False

    def check_all_players_locked(self):
        """Auto-advance Work phase if everyone has a job/action."""
        if all(p.action_locked for p in self.players.values()):
            self.next_phase()

    def cleanup_messages(self):
        """Deletes messages not interacted with."""
        # Keep COMPLETED, ACCEPTED (for history), and pending SYSTEM messages
        # Remove ignored pending offers
        self.messages = [m for m in self.messages
                         if m.status in ['ACCEPTED', 'COMPLETED', 'DENIED']
                         or (m.status == 'PENDING' and m.is_system)]

    # --- Phase Logic ---

    def resolve_work_phase(self):
        # 1. Resolve Conflicts (Seizing)
        for tile_id, conflict in list(self.active_conflicts.items()):
            for tile_id, conflict in list(self.active_conflicts.items()):
                att_count = len(conflict['attackers'])
                def_count = len(conflict['defenders'])

# Owner automatically counts as defender if not locked elsewhere
                tile = next(t for t in self.map_tiles if t['id'] == tile_id)
                if tile['owner_id'] and not self.players[tile['owner_id']].action_locked:
                    def_count += 1

                if att_count > def_count:
                    conflict['days_held'] += 1
                    if conflict['days_held'] >= 3:
                        # Transfer Ownership
                        tile['owner_id'] = conflict['attacker_id']
                        # Reset development level? (Optional, assumed keeps level)
                        del self.active_conflicts[tile_id]
                else:
                    # Defenders held the line, progress reset
                    conflict['days_held'] = 0

        # 2. Generate Resources
        for tile in self.map_tiles:
            if tile['owner_id'] and tile['id'] not in self.active_conflicts:
                # Simplified level logic
                amount = 2 if tile.get('level') == 2 else 1
                res_type = tile['type'].lower()
                if res_type == 'woods':
                    res_type = 'wood'
                if res_type == 'farm':
                    res_type = 'food'

                # Add to owner inventory
                if tile['owner_id'] in self.players:
                    self.players[tile['owner_id']
                                 ].resources[res_type] += amount

    def resolve_trade_phase(self):
        # Force complete any pending Accepted trades?
        pass

    def resolve_night_phase(self):
        for p in self.players.values():
            p.consume_daily()

    def generate_payout_messages(self):
        """
        Called at start of Trade.
        Finds accepted work offers and creates 'Payout' tasks for employers.
        """
        for msg in self.messages:
            if msg.type == 'EMPLOYMENT' and msg.status == 'ACCEPTED':
                # Valid contract found.
                # In this game, the original Employment Message becomes the interface
                # for the employer to pay. We just ensure it's visible.
                pass

    # --- Map & Helper ---
    def generate_map(self):
        player_count = len(self.players)

        # 1. Determine Tile Counts
        # "Enough farm tiles... for everyone to acquire" (assuming 2 food/tile
        # vs 1 food consumption)
        # We ensure at least 1 farm per player to be safe and allow competition
        num_farms = player_count // 2

        # "Rest available for wood, then one or two for mines"
        num_woods = player_count + 1
        num_mines = 2

        tiles_to_place = ["Farm"] * num_farms + \
            ["Woods"] * num_woods + ["Mine"] * num_mines
        random.shuffle(tiles_to_place)

        # 2. Generate Hex Spiral Coordinates (q, r)
        # This creates a compact cluster of hexagons
        self.map_tiles = []
        q, r = 0, 0

        # Spiral directions for flat-topped hexes
        directions = [
            (+1, 0), (+1, -1), (0, -1),
            (-1, 0), (-1, +1), (0, +1)
        ]

        # Add center tile
        if tiles_to_place:
            self.map_tiles.append({
                "id": "t_0_0", "q": 0, "r": 0,
                "type": tiles_to_place.pop(0), "owner_id": None
            })

        # Spiral outwards
        radius = 1
        while tiles_to_place:
            # Move to start of ring (radius, 0) is not quite right for
            # hex spiral,
            # standard algo starts at q=0, r=0 then moves to neighbor 4,
            # then spirals
            q, r = -radius, radius  # Start position for ring

            for dx, dy in directions:
                for _ in range(radius):
                    if not tiles_to_place:
                        break

                    # Calculate new coord
                    q += dx
                    r += dy

                    # Add tile
                    self.map_tiles.append({
                        "id": f"t_{q}_{r}",
                        "q": q, "r": r,
                        "type": tiles_to_place.pop(0),
                        "owner_id": None
                    })
                if not tiles_to_place:
                    break
            radius += 1

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
            yield f"Happy golbin {i}"

    def get_state_for_player(self, session_id):
        me = self.players.get(session_id)
        if not me:
            return None

        # Filter messages for this player
        my_messages = [m.to_dict() for m in self.messages
                       if m.to_id == session_id or m.from_id == session_id]

        # NEW: Create a list of other players for the dropdowns
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
            "me": me.to_dict(),
            "map": self.map_tiles,
            "messages": my_messages,
            "conflicts": self.active_conflicts,
            "player_count": len(self.players),
            "player_list": other_players,  # <--- Added this
            "is_host": session_id == self.host_id
        }
