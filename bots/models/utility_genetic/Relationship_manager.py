from random import random
from .Relationship import Relationship


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
        self.processed_fire_ids = {}

        self.sympathy = {}

    def update_relationships(self, state):
        me = state.get("me")
        for trade in me.get('trade_history', []):
            trade_id = trade.get("id")
            if trade_id in self.processed_action_ids:
                continue
            self._process_trade(trade, state)

        for player in state.get('player_list', []):
            if player.get('id') != me.get('session_id'):
                self.sympathy[player.get('id')] = player.get("health", "healthy") == 'sick'

        for interaction in me.get('fire_history', []):
            self.process_fire_interaction(interaction, state)

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
    
    def will_honor_work_hire(self, player_id):
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

    
    def will_honor_trade(self, player_id):
        relationship = self.get_relationship(player_id)
        score = (
        relationship.trust * self.genome.trust_weight +
        relationship.friendship * self.genome.friendship_weight +
        relationship.generosity * self.genome.generosity_weight -
        relationship.greed * self.genome.greed_weight
        )
        if self.sympathy.get(player_id, False):
            score += self.genome.trade_sympathy_weight
        max_score = (
            self.genome.trust_weight +
            self.genome.friendship_weight +
            self.genome.generosity_weight +
            self.genome.greed_weight+
            self.genome.trade_sympathy_weight
        )
        if max_score != 0:
            probability = (score + max_score) / (2 * max_score)
            probability = 0.25 + 0.75 * probability # Weight it biased towards being honest (so default relationships arent constantly lying but still change the odds)
            probability = max(0.0, min(1.0, probability))
        else:
            probability = 0.5
        will_honor = random() <= probability
        return will_honor
    
    def get_relationship_score(self, player_id):
        relationship = self.get_relationship(player_id)
        
        if not relationship:
            return 0
        
        score = (
            relationship.trust * self.genome.trust_weight +
            relationship.friendship * self.genome.friendship_weight +
            relationship.generosity * self.genome.generosity_weight -
            relationship.greed * self.genome.greed_weight
        )
        return score
    
    def sort_liked_players(self, players):
        return sorted(
            [
                (
                    self.fire_score(p.get("id")),
                    p
                )
                for p in players
            ],
            key=lambda x: x[0],
            reverse=True
        )
    
    def fire_score(self, player_id):
        relationship = self.get_relationship(player_id)
        score = relationship.trust * self.genome.fire_trust_weight + relationship.friendship * self.genome.fire_friendship_weight
        if self.sympathy.get(player_id, False):
            score += self.genome.fire_sympathy_weight
        score /= (self.genome.fire_trust_weight +
                  self.genome.fire_friendship_weight +
                  self.genome.fire_sympathy_weight 
                )
        return score
    
    def process_fire_interaction(self, interaction, state):
        me = state.get('me')
        im_host = interaction.get("role") == "host"
        fire_id = interaction.get("fire_id")

        if fire_id not in self.processed_fire_ids:
            self.processed_fire_ids[fire_id] = set()

        if im_host:
            for player_id in interaction.get("guests", []):
                if player_id == me.get('id'):
                    continue
                if player_id in self.processed_fire_ids[fire_id]:
                    continue
                else:
                    relationship = self.get_relationship(player_id)
                    relationship.trust += self.genome.fire_trust_sensitivity/2
                    relationship.friendship += self.genome.fire_friendship_sensitivity/2
                    self.processed_fire_ids[fire_id].add(player_id)
        else:
            host_id = interaction.get("host_id")
            if host_id not in self.processed_fire_ids[fire_id]:
                relationship = self.get_relationship(host_id)
                relationship.trust += self.genome.fire_trust_sensitivity
                relationship.friendship += self.genome.fire_friendship_sensitivity
                relationship.generosity += self.genome.fire_generosity_sensitivity
                relationship.greed -= self.genome.fire_greed_sensitivity
                fire_id = interaction.get("fire_id")
                for player_id in interaction.get("guests", []):
                    if player_id == me.get('id'):
                        continue
                    if player_id == host_id:
                        continue
                    relationship = self.get_relationship(player_id)
                    relationship.trust += self.genome.fire_trust_sensitivity/3
                    relationship.friendship += self.genome.fire_friendship_sensitivity/3
                    self.processed_fire_ids[fire_id].add(player_id)