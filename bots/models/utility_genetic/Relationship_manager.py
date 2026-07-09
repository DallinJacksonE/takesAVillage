from random import random
from bots.models.utility_genetic.utility_genetic.Relationship import Relationship
from bots.models.utility_genetic.utility_genetic.Relationship import Relationship


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
        
        for relationship in self.relationships.values():
            self.normalize(relationship)
        
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
        relationship.friendship -= amount * self.genome.friendship_sensitivity
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
    
    def normalize(self, relationship):
        relationship.trust = max(-1, min(1, relationship.trust))
        relationship.friendship = max(-1, min(1, relationship.friendship))
        relationship.greed = max(0, min(1, relationship.greed))
        relationship.generosity = max(0, min(1, relationship.generosity))

    def get_relationship(self, player_id):
        if player_id not in self.relationships:
            self.relationships[player_id] = Relationship(
                trust=self.genome.initial_trust,
                friendship=self.genome.initial_friendship,
                generosity=self.genome.initial_generosity,
                greed=self.genome.initial_greed,
            )
        return self.relationships[player_id]
    
    def will_honor_trade(self, player_id):
        relationship = self.get_relationship(player_id)
        score = (
        relationship.trust * self.genome.trust_weight +
        relationship.friendship * self.genome.friendship_weight +
        relationship.generosity * self.genome.generosity_weight -
        relationship.greed * self.genome.greed_weight
        )
        max_score = (
            self.genome.trust_weight +
            self.genome.friendship_weight +
            self.genome.generosity_weight +
            self.genome.greed_weight
        )
        if max_score != 0:
            probability = (score + max_score) / (2 * max_score)
            probability = max(0.0, min(1.0, probability))
        else:
            probability = 0.5
        will_honor = random() <= probability
        return will_honor