from models.genetic.Relationship import Relationship
from models.genetic.Relationship import Relationship


class RelationshipManager:

    def __init__(self, bot):
        self.bot = bot
        self.genome = bot.genome

        self.relationships = {}

        self.processed_ids = set()

        # Keep track of processed events
        self.processed_trade_ids = set()
        self.processed_action_ids = set()
        self.processed_timeline_ids = set()

    def update_relationships(self, state):
        me = state.get("me")
        for trade in me.get('trade_history', []):
            trade_id = trade.get("id")
            if trade_id in self.processed_action_ids:
                continue
            self._process_trade(trade, state)
        
        print(f"Processed relationships for bot {me.get('session_id')}")
        print(self.relationships)

    def _process_trade(self, trade, gamestate):
        me = gamestate.get("me")
        promised = trade.get("requested")
        received = trade.get("actual_received")
        if trade["initiator_id"] == me.get("session_id"):
            player_id = trade["target_id"]
        else:
            player_id = trade["initiator_id"]

        honest = True

        for resource in promised.keys():
            amount = promised.get(resource, 0)
            if resource in received:
                amount -= received.get(resource, 0)
                if amount == 0:
                    continue
                else:
                    honest = False
                    self._update_trade_relationship(player_id, resource, amount)
        if honest:
            self._honest_update(player_id)
        self.processed_action_ids.add(trade.get("id"))
        return

    def _update_trade_relationship(self, player_id, resource, amount):
        if player_id not in self.relationships:
            self.relationships[player_id] = Relationship(
                trust=self.genome.initial_trust,
                friendship=self.genome.initial_friendship,
                generosity=self.genome.initial_generosity,
                greed=self.genome.initial_greed
            )

        relationship = self.relationships[player_id]
        relationship.trust -= amount * self.genome.trust_sensitivity
        relationship.friendship -= amount * self.genome.friendship_sensitivity/2
        relationship.greed += amount * self.genome.greed_sensitivity
    
    def _honest_update(self, player_id):
        if player_id not in self.relationships:
            self.relationships[player_id] = Relationship(
                trust=self.genome.initial_trust,
                friendship=self.genome.initial_friendship,
                generosity=self.genome.initial_generosity,
                greed=self.genome.initial_greed
            )

        relationship = self.relationships[player_id]
        relationship.trust += self.genome.honest_trust_increase
        relationship.friendship += self.genome.honest_friendship_increase
