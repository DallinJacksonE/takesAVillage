import copy

from BaseBot import BaseBot
from bots.models.utility_genetic.Relationship_manager import RelationshipManager
from bots.models.utility_genetic.Genome import Genome


class GeneticBot(BaseBot):
    def __init__(self, genome):
        self.type_to_resource = {"woods": "wood", "farm": "food", "mine": "iron"}
        self.trade_intentions = {}
        super().__init__(genome)
        self.relationship_manager = RelationshipManager(self)

    @staticmethod
    def from_json(genome_json):
        return GeneticBot(Genome(**genome_json))

    def adjusted_resource_value(self, bundle, me):
        resources = me.get("resources", {})

        food_need = max(0, 5 - resources.get("food", 0))
        wood_need = max(0, 5 - resources.get("wood", 0))
        iron_need = max(0, 5 - resources.get("iron", 0))

        g = self.genome

        return (
            bundle.get("food", 0)
            * (g.food_weight + food_need * g.food_desperation_weight)
            +
            bundle.get("wood", 0)
            * (g.wood_weight + wood_need * g.wood_desperation_weight)
            +
            bundle.get("iron", 0)
            * (g.iron_weight + iron_need * g.iron_desperation_weight)
        )
    
    def resource_value(self,bundle):
        return (
            bundle.get("food", 0) * self.genome.food_weight +
            bundle.get("wood", 0) * self.genome.wood_weight +
            bundle.get("iron", 0) * self.genome.iron_weight
        )

    def choose_action(self, game_state: dict) -> dict | None:
        """
        Evaluates actions using genetic weights and returns a
        formatted payload.
        """
        me = game_state.get("me", {})

        if game_state.get("status") == "WAITING":
            return None

        actions = self.get_available_actions(game_state)

        if me.get("health") == "dead":
            return None
        
        self.relationship_manager.update_relationships(game_state)

        if  game_state.get("phase") == "NIGHT":
            accept_actions = [
                a for a in actions
                if a["action_command"] == "ACCEPT"
            ]
            if accept_actions:
                return self.format_network_payload(accept_actions[0])
        elif game_state.get("phase") == "WORK":

            response_actions = [
                a for a in actions
                if a["action_command"] in ("ACCEPT", "DENY")
            ]

            if response_actions:
                best = max(
                    response_actions,
                    key=lambda a: self.score_action(a, game_state)
                )
                return self.format_network_payload(best)

        elif game_state.get("phase") == "TRADE":

            finalize_action = next(
                (
                    a for a in actions
                    if a["action_command"] == "FINALIZE"
                ),
                None
            )

            if finalize_action:
                return self.format_network_payload(finalize_action)

            trade_responses = [
                a for a in actions
                if a["action_command"] in ["ACCEPT", "DENY"]
            ]

            if trade_responses:
                for action in trade_responses:
                    if action["action_command"] != "ACCEPT":
                        continue
                    trade_id = action["payload"].get("action_id")
                    if trade_id in self.trade_intentions:
                        if not self.trade_intentions[trade_id]:
                            return self.format_network_payload(action)
                        
                # Return the best response if not planning to lie
                best_response = max(
                    trade_responses,
                    key=lambda a: self.score_action(a, game_state)
                )

                return self.format_network_payload(best_response)

        if me.get("finished_phase"):
            return None

        print(f"available actions for bot: {actions}")

        if self.waiting:
            return None
        
        # 2. If no valid moves, finish the phase
        if not actions:
            return self.format_network_payload(None)

        # 3. Score and select the best action
        best_action = max(
            actions,
            key=lambda a: self.score_action(a, game_state)
        )

        # 4. Use the base class to clean and format the DTO
        return self.format_network_payload(best_action)

    def score_action(self, action: dict, game_state: dict) -> float:
        """Scores an action dict using the bot's genome."""
        g = self.genome
        score = 0
        command = action["action_command"]
        contract = None
        me = game_state.get("me", {})

        if "action_id" in action.get("payload", {}):
            action_id = action["payload"]["action_id"]

            contract = next(
                (
                    a for a in me.get("actions", [])
                    if a.get("id") == action_id
                ),
                None
            )

        contract_type = contract.get("type") if contract else None
            
        resources = me.get("resources", {"wood": 0, "food": 0, "iron": 0})

        food = resources.get("food", 0)
        wood = resources.get("wood", 0)
        iron = resources.get("iron", 0)

        # =====================
        # NEEDS
        # =====================
        food_need = max(0, 5 - food)
        wood_need = max(0, 5 - wood)
        iron_need = max(0, 5 - iron)

        if command == "EMPLOYMENT":
            score += g.work_weight

            wage = action["payload"].get("wage", 0)
            wage_type = action["payload"].get("wage_type")

            if wage_type == "food":
                score += (wage * g.food_weight)
                score += (food_need * g.food_desperation_weight)
            elif wage_type == "wood":
                score += (wage * g.wood_weight)
                score += (wood_need * g.wood_desperation_weight)
            elif wage_type == "iron":
                score += (wage * g.iron_weight)
                score += (iron_need * g.iron_desperation_weight)

            score -= .25 # prefer working for self all else equal

        # =====================
        # BUILD
        # =====================
        elif command == "BUILD_DEV":
            score += g.build_weight

            # Retrieve the injected hidden type from BaseBot
            tile_type = action["payload"].get("_tile_type")

            if tile_type == "Farm":
                score += (g.farm_preference + g.growth_weight)
                if food_need > 0:
                    score += (food_need * g.survival_weight)
            elif tile_type == "Woods":
                score += (g.woods_preference + g.growth_weight)
            elif tile_type == "Mine":
                score += (g.mine_preference + g.growth_weight)

        # =====================
        # UPGRADE / MAINTAIN / CONTEST
        # =====================
        elif command == "UPGRADE_DEV":
            score += (g.upgrade_weight + g.growth_weight)

            dev_id = action["payload"]["dev_id"]

            dev = next(
                (
                    d for d in game_state.get("developments", [])
                    if d["id"] == dev_id
                ),
                None
            )

            if dev:
                
                dev_type = dev.get("type")

                if dev_type == "Farm":
                    score += g.farm_preference
                elif dev_type == "Woods":
                    score += g.woods_preference
                elif dev_type == "Mine":
                    score += g.mine_preference

                level = dev.get("level", 1)
                days_left = dev.get("maintenance_days")

                # Growth value
                score += level * g.future_reward_weight

                urgency_bonus = max(0, 5 - days_left)

                score += (
                    urgency_bonus
                    * (g.maintain_weight
                    + g.upgrade_weight)
                    )

        elif command == "MAINTAIN_DEV":
            score += (g.maintain_weight + g.future_reward_weight)

            dev_id = action["payload"]["dev_id"]

            dev = next(
                (
                    d for d in game_state.get("developments", [])
                    if d["id"] == dev_id
                ),
                None
            )

            if dev:
                days_left = dev.get("maintenance_days")
                score += (
                    max(0, 5 - days_left)
                    * g.maintain_weight
                )

        elif command == "CONTEST_DEV":

            side = action["payload"].get("side")
            dev_id = action["payload"].get("dev_id")

            dev = next(
                (d for d in game_state.get("developments", [])
                if d["id"] == dev_id),
                None
            )

            if dev:
                score += dev.get("level", 1) * g.future_reward_weight

                if side == "OWNER":

                    if dev["owner_id"] == me["id"]:
                        score += (
                            dev["level"]
                            * g.future_reward_weight
                            * 3
                        )

                    score += g.cooperation_weight

                elif side == "INITIATOR":
                    score += (
                        g.contest_weight +
                        g.aggression_weight
                    )

                elif side == "CONTESTER":
                    score += (
                        g.contest_weight +
                        g.cooperation_weight
                    )

        # =====================
        # CAMPFIRE
        # =====================
        elif command == "START_FIRE":
            score += (g.fire_weight + g.cooperation_weight +
                      g.reputation_weight)

        # =====================
        # WORK
        # =====================
        elif command == "COMMIT_WORK":
            score += g.work_weight
            job = action["payload"]["job"]
            wage = job.get("wage", 0)
            wage_type = job.get("wage_type")

            if wage_type == "food":
                score += (wage * g.food_weight)
                score += (food_need * g.food_desperation_weight)
            elif wage_type == "wood":
                score += (wage * g.wood_weight)
                score += (wood_need * g.wood_desperation_weight)
            elif wage_type == "iron":
                score += (wage * g.iron_weight)
                score += (iron_need * g.iron_desperation_weight)

        
        if contract:

            if contract_type == "EMPLOYMENT":

                dev = next(
                    (
                        d for d in game_state.get("developments", [])
                        if d["id"] == contract.get("dev_id")
                    ),
                    None
                )

                if not dev:
                    return -9999

                produced_resource = self.type_to_resource[dev["type"].lower()]
                produced_amount = dev["level"]

                produced_value = self.marginal_utility(
                    produced_resource,
                    produced_amount,
                    me
                )

                me_copy = copy.deepcopy(me)
                me_copy['resources'][produced_resource] += produced_amount

                wage_value = self.marginal_cost(
                    contract["wage_type"],
                    contract["wage"],
                    me_copy
                )

                net_value = produced_value + wage_value
                
                # checks to only accept affordable trades
                future_food = food
                future_wood = wood
                future_iron = iron

                if produced_resource == "food":
                    future_food += produced_amount
                elif produced_resource == "wood":
                    future_wood += produced_amount
                elif produced_resource == "iron":
                    future_iron += produced_amount
                
                can_afford = (
                    (contract["wage_type"] == "food" and future_food >= contract["wage"])
                    or
                    (contract["wage_type"] == "wood" and future_wood >= contract["wage"])
                    or
                    (contract["wage_type"] == "iron" and future_iron >= contract["wage"])
                )
                
                if not can_afford:
                    if command == "ACCEPT":
                        return -100000
                    else:  # DENY
                        return 100000
                    
                # symmetric decision scoring
                if command == "ACCEPT":
                    score += net_value + 0.01   # tie breaker for now
                elif command == "DENY":
                    score -= net_value

            elif contract_type == "TRADE":

                if contract["initiator_id"] == me["id"]:
                    given = contract.get("offer_items", {})
                    received = contract.get("request_items", {})
                else:
                    given = contract.get("request_items", {})
                    received = contract.get("offer_items", {})

                can_fulfill = all(
                    resources.get(r, 0) >= qty
                    for r, qty in given.items()
                )
                
                if not can_fulfill:
                    if command == "ACCEPT":
                        return -100000
                    elif command == "DENY":
                        return 100000

                future_me = {
                    **me,
                    "resources": resources.copy()
                }

                received_value = 0
                given_cost = 0

                # Gain utility and update simulated inventory
                for resource, amount in received.items():
                    received_value += self.marginal_utility(resource, amount, future_me)
                    future_me["resources"][resource] += amount

                # Cost is evaluated after receiving the goods
                for resource, amount in given.items():
                    given_cost += self.marginal_cost(resource, amount, future_me)
                    future_me["resources"][resource] -= amount

                utility = received_value - given_cost

                if command == "ACCEPT":
                    score += utility + g.cooperation_weight
                else:
                    score -= utility

        if command == "FINALIZE":
            # Prefer to finalize (ship goods) if we can actually send the items
            actual = action.get("payload", {}).get("actual_items", {})
            feasible = {
                r: min(int(qty), resources.get(r, 0))
                for r, qty in actual.items()
            }
            feasible_value = self.resource_value(feasible)

            if feasible_value > 0:
                # Strongly favor finalizing when we can ship what we promised
                score += 15000
                score += feasible_value * 50
            else:
                # If we can't ship anything, deprioritize
                score -= 1000
        # =====================
        # RANDOMNESS
        # =====================
        score += (g.risk_weight * 0.1)

        return score
    
    def marginal_utility(self, resource: str, amount: int, me: dict):
        resources = me.get("resources")
        g = self.genome
        current = resources.get(resource, 0)
        total = 0
        for i in range(amount):
            inventory = current + i
            if resource == "food":
                val = g.food_weight + max(0, 5 - inventory) * g.food_desperation_weight
            elif resource == "wood":
                val = g.wood_weight + max(0, 5 - inventory) * g.wood_desperation_weight
            elif resource == "iron":
                val = g.iron_weight + max(0, 5 - inventory) * g.iron_desperation_weight
            total += val
        return total
    
    def marginal_cost(self, resource: str, amount: int, me: dict):
        resources = me.get("resources")
        g = self.genome
        current = resources.get(resource, 0)
        total = 0
        for i in range(amount):
            inventory = current - i
            if resource == "food":
                val = g.food_weight + max(0, 5 - inventory) * g.food_desperation_weight
            elif resource == "wood":
                val = g.wood_weight + max(0, 5 - inventory) * g.wood_desperation_weight
            elif resource == "iron":
                val = g.iron_weight + max(0, 5 - inventory) * g.iron_desperation_weight
            total -= val
        return total
    
    def get_available_actions(self, game_state: dict) -> list[dict]:
        """
        Reconstructs the available actions purely from the JSON state DTO.
        """
        if game_state.get("status") == "WAITING":
            return []
        actions = []
        phase = game_state.get("phase")
        me = game_state.get("me", {})
        resources = me.get("resources", {"wood": 0, "food": 0, "iron": 0})

        pending_application = any(
            action.get("type") == "EMPLOYMENT"
            and action.get("is_application")
            and action.get("initiator_id") == me.get("id")
            and action.get("status") == "PENDING"
            for action in me.get("actions", [])
        )

        if pending_application:
            self.waiting = True
            return []
        
        self.waiting = False

        # reset per-phase counters when phase changes
        if phase != self._last_phase:
            self._last_phase = phase
            if phase == "TRADE":
                self.trade_offers_made = 0
                self.trade_intentions.clear()

        if phase == "WORK" and me.get("health") != "dead":
            # --- 1. BUILD ACTIONS ---
            dev_costs = game_state.get("development_costs", {})
            map_data = game_state.get("map", {})

            # Handle map_data whether it arrives as a dict or a list
            tiles = map_data.values() if isinstance(
                map_data, dict) else map_data
            
            if me.get("health") not in ["sick", "recovering"]:

                for tile in tiles:
                    if not tile.get("development"):
                        tile_type = tile.get("type")
                        build_cost = dev_costs.get(tile_type, {}).get("build", {})

                        affordable = all(
                            resources.get(res, 0) >= amount
                            for res, amount in build_cost.items()
                        )

                        if affordable:
                            actions.append({
                                "action_command": "BUILD_DEV",
                                "payload": {
                                    "tile_id": tile["id"],
                                    "_tile_type": tile_type
                                }
                            })
                for dev in game_state.get("developments", []):
                    if dev["owner_id"] == me["id"] and dev["can_upgrade"]:
                        upgrade_cost = self.get_upgrade_cost(dev, game_state)

                        affordable = all(
                            resources.get(res, 0) >= amount
                            for res, amount in upgrade_cost.items()
                        )

                        if affordable:
                            actions.append({
                                "action_command": "UPGRADE_DEV",
                                "payload": {
                                    "dev_id": dev["id"]
                                }
                            })
                
                    if dev["owner_id"] == me["id"]:
                        affordable = all(
                            resources.get(r, 0) >= amt
                            for r, amt in self.get_maintenance_cost(dev, game_state).items()
                        )

                        if affordable:
                            actions.append({
                                "action_command": "MAINTAIN_DEV",
                                "payload": {
                                    "dev_id": dev["id"]
                                }
                            })
                
                    if dev["owner_id"] != me["id"]:
                        actions.append({
                            "action_command": "CONTEST_DEV",
                            "payload": {
                                "dev_id": dev["id"],
                                "side": "INITIATOR"
                            }
                        })

                # --- JOB APPLICATIONS ---

                existing_apps = {
                    (a.get("dev_id"), a.get("target_id"))
                    for a in me.get("actions", [])
                    if a["type"] == "EMPLOYMENT"
                }

                for dev in game_state.get("developments", []):

                    owner = self.find_player(game_state, dev["owner_id"])

                    if (dev['id'], dev['owner_id']) in existing_apps:
                        continue

                    if dev["is_contested"]:

                        if dev["owner_id"] == me["id"]:
                            actions.append({
                                "action_command": "CONTEST_DEV",
                                "payload": {
                                "dev_id": dev["id"],
                                "side": "OWNER"
                            }
                        })
                        
                        elif dev.get("contest_initiator_id") == me["id"]:
                            actions.append({
                                "action_command": "CONTEST_DEV",
                                "payload": {
                                    "dev_id": dev["id"],
                                    "side": "CONTESTER"
                                }
                            })

                        else:
                            actions.append({
                                "action_command": "CONTEST_DEV",
                                "payload": {
                                    "dev_id": dev["id"],
                                    "side": "OWNER"
                                }
                            })

                            actions.append({
                                "action_command": "CONTEST_DEV",
                                "payload": {
                                    "dev_id": dev["id"],
                                    "side": "CONTESTER"
                                }
                            })

                    if dev.get("worker_id"):
                        continue
                    if not self.is_dead_player(owner):
                        actions.append({
                            "action_command": "EMPLOYMENT",
                            "payload": {
                                "type": "EMPLOYMENT",
                                "target_id": dev["owner_id"],
                                "dev_id": dev["id"],
                                "wage": dev['level'],
                                "wage_type": self.resource_map[dev['type']],
                                "is_application": True
                            }
                        })

                # --- 2. WORK ACTIONS ---
                for job in me.get("available_work", []):
                    owner_id = job.get('development', {}).get('owner_id')
                    owner = self.find_player(game_state, owner_id)
                    if self.is_dead_player(owner):
                        continue
                    if not job.get('development').get('is_contested'):
                        actions.append({
                            "action_command": "COMMIT_WORK",
                            "payload": {"job": job}
                        })
                
            for action in me.get("actions", []):
                 if (
                    action["type"] == "EMPLOYMENT"
                    and action["status"] == "PENDING"
                    and action["target_id"] == me["id"]
                ):
                    actions.append({
                        "action_command": "ACCEPT",
                        "payload": {
                            "action_id": action["id"]
                        }
                    })
                    actions.append({
                        "action_command": "DENY",
                        "payload": {
                            "action_id": action["id"]
                        }
                     })

        elif phase == "TRADE" and me.get("health") != "dead":
            for action in me.get("actions", []):
                if (
                    action["type"] == "TRADE"
                    and action["waiting_on_id"] == me["id"]
                ):
                    trade_id = action["id"]

                    if trade_id not in self.trade_intentions:

                        other_player = (
                            action["initiator_id"]
                            if action["initiator_id"] != me["id"]
                            else action["target_id"]
                        )

                        will_honor = self.relationship_manager.will_honor_trade(other_player)

                        self.trade_intentions[trade_id] = will_honor

                    actions.append({
                        "action_command": "ACCEPT",
                        "payload": {
                            "action_id": trade_id
                        }
                    })
                    actions.append({
                        "action_command": "DENY",
                        "payload": {
                            "action_id": action["id"]
                        }
                    })
                if action["status"] == "ACCEPTED":

                    is_initiator = action.get("initiator_id") == me.get("id")

                    already_finalized = (
                        action.get("initiator_finalized", False)
                        if is_initiator
                        else action.get("target_finalized", False)
                    )

                    if already_finalized:
                        continue

                    promised = (
                        action.get("offer_items")
                        if is_initiator
                        else action.get("request_items")
                    )

                    feasible = {}
                    resources = me.get("resources", {})

                    for r, qty in (promised or {}).items():
                        try:
                            q = int(qty)
                        except Exception:
                            q = 0

                        available = int(resources.get(r, 0))
                        send_amt = max(0, min(q, available))

                        if send_amt > 0:
                            feasible[r] = send_amt
                    
                    will_honor = self.trade_intentions.get(action["id"], True)

                    if will_honor:

                        actions.append({
                            "action_command": "FINALIZE",
                            "payload": {
                                "action_id": action["id"],
                                "actual_items": feasible
                            }
                        })
                    else:
                        actions.append({
                            'action_command': 'FINALIZE',
                            'payload': {
                                'action_id': action["id"],
                                'actual_items': {}
                            }
                        })
            # --- 1. Draft simple trades ---
            # Bots may propose trades to other players offering surplus
            # and requesting resources they lack.
            resources = me.get("resources", {"wood": 0, "food": 0, "iron": 0})
            # determine offer (most abundant) and request (least abundant)
            costs = {r: self.marginal_cost(r, 1, me) for r in resources.keys() if resources.get(r, 0) > 0}
            benefits = {
                r: self.marginal_utility(r, 1, me) for r in resources
            }

            best_requests = sorted(
                benefits.items(),
                key=lambda x: x[1],
                reverse=True
            )

            best_offers = sorted(
                costs.items(),
                key=lambda x: x[1]
            )

            if not best_offers:
                return [{
                    "action_command": "FINISH_PHASE",
                    "payload": {}
                }]

            offer_item = best_offers[0][0]

            best_requests = [
                (r, value) for r, value in best_requests if r != offer_item
            ]

            request_item= best_requests[0][0]             
            
            existing_outgoing_trade = any(
                a.get("type") == "TRADE" and a.get("initiator_id") == me.get("id")
                and a.get("status") in ["PENDING", "NEGOTIATING", "ACCEPTED"]
                for a in me.get("actions", [])
            )

            if existing_outgoing_trade:
                # Respect a single outstanding trade until it's resolved
                pass
            else:
                # Throttle number of trades per bot per TRADE phase
                if self.trade_offers_made < self.max_trade_offers_per_phase:
                    for player in self.get_alive_players(game_state):
                        if player.get("id") == me.get("id"):
                            continue

                        # Avoid creating duplicate pending trades to same target
                        existing = any(
                            a.get("type") == "TRADE" and a.get("target_id") == player.get("id")
                            for a in me.get("actions", [])
                        )
                        if existing:
                            continue

                        ##           IMPLEMENT TRUSTING MECHANICS HERE                  ##

                        actions.append({
                                "action_command": "TRADE",
                                "payload": {
                                    "type": "TRADE",
                                    "target_id": player.get("id"),
                                    "offer_items": {offer_item: 1},
                                    "request_items": {request_item: 1}
                                }
                            })
                        # Count this draft so we don't spam the phase
                        self.trade_offers_made += 1
                        # Stop creating more offers once limit reached
                        if self.trade_offers_made >= self.max_trade_offers_per_phase:
                            break
                

        elif phase == "NIGHT":
            # --- CAMPFIRE ACTIONS ---
            fire_cost = game_state.get("campfire_cost", {"wood": 1})
            affordable = all(
                resources.get(res, 0) >= amount
                for res, amount in fire_cost.items()
            )

            if me.get("fire_status") == "COLD" and affordable:
                actions.append({
                    "action_command": "START_FIRE",
                    "payload": {}
                })
            for action in me.get("actions", []):
                if (
                    action["type"] == "CAMPFIRE"
                    and action["waiting_on_id"] == me["id"]
                ):
                    # Only offer ACCEPT when the host still has seats available
                    is_request = action.get("is_request", False)
                    host_id = action.get("target_id") if is_request else action.get("initiator_id")
                    host_player = None
                    for p in game_state.get("player_list", []):
                        if p.get("id") == host_id:
                            host_player = p
                            break

                    can_accept = False
                    if host_player and host_player.get("fire_status") == "HOST":
                        max_seats = game_state.get("max_fire_seats", 0)
                        current = len(host_player.get("fire_guests", []) or [])
                        if current < max_seats:
                            can_accept = True

                    if can_accept:
                        actions.append({
                            "action_command": "ACCEPT",
                            "payload": {
                                "action_id": action["id"]
                            }
                        })

                    # Always allow denying an invite
                    actions.append({
                        "action_command": "DENY",
                        "payload": {
                            "action_id": action["id"]
                        }
                    })
            
            for player in self.get_alive_players(game_state):
                if player["id"] == me["id"]:
                    continue
                if me["fire_status"] == "HOST":
                    actions.append({
                        "action_command": "CAMPFIRE",
                        "payload": {
                            "target_id": player["id"],
                            "is_request": False,
                            "type": "CAMPFIRE"
                        }
                    })
                
                elif player["fire_status"] == "HOST" and me["fire_status"] == "COLD":
                    actions.append({
                        "action_command": "CAMPFIRE",
                        "payload": {
                            "target_id": player["id"],
                            "is_request": True,
                            "type": "CAMPFIRE"
                        }
                    })
        return actions
        
