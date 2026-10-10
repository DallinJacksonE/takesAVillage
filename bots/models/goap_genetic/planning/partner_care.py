from ..memory import Memory


CARE_HEALTH_STATES = {"sick", "recovering"}


class PartnerCareAnalyzer:
    """Derives factual partner vulnerability and care opportunities.

    This helper intentionally keeps policy light: it identifies trusted partners
    who visibly need food or fire support, while leaving final action preference
    to goal/action scoring.
    """

    def analyze(self, memory: Memory) -> dict:
        vulnerabilities = {}
        care_needs = {}
        trusted_sick_partners = []
        free_food_targets = []
        campfire_targets = []

        for player in memory.get("players", []) or []:
            player_id = player.get("id")
            if not player_id or player_id == memory.get("my_id"):
                continue
            trust = self._trust(player_id, memory)
            hostility = self._hostility(player_id, memory)
            if trust <= 0.0 or hostility > 0.5:
                continue

            needs = {}
            health = player.get("health")
            is_sick = health in CARE_HEALTH_STATES
            if is_sick:
                trusted_sick_partners.append(player_id)
            if self._needs_food(player):
                needs["food"] = self._food_need(player)
            if self._needs_fire(player, memory):
                needs["campfire"] = self._fire_need(player)
            if not needs:
                continue

            complementarity = float((memory.get("complementary_partner_scores", {}) or {}).get(
                player_id, 0.0) or 0.0)
            vulnerabilities[player_id] = {
                "health": health,
                "needs_food": needs.get("food", 0.0),
                "needs_fire": needs.get("campfire", 0.0),
                "trust": trust,
                "complementarity": complementarity,
            }
            care_needs[player_id] = needs
            if "food" in needs:
                free_food_targets.append(player_id)
            if "campfire" in needs:
                campfire_targets.append(player_id)

        return {
            "partner_vulnerability": vulnerabilities,
            "trusted_sick_partners": trusted_sick_partners,
            "campfire_support_targets": self._rank_targets(campfire_targets, vulnerabilities),
            "free_food_support_targets": self._rank_targets(free_food_targets, vulnerabilities),
            "partner_care_needs": care_needs,
        }

    def _trust(self, player_id: str, memory: Memory) -> float:
        trusted = memory.get("trusted_partner_scores", {}) or {}
        if player_id in trusted:
            return float(trusted.get(player_id, 0.0) or 0.0)
        relationship = (memory.get("relationships", {}) or {}).get(player_id, {}) or {}
        confidence = float(relationship.get("confidence", 0.0) or 0.0)
        return float(relationship.get("trust", 0.0) or 0.0) * max(0.25, confidence)

    def _hostility(self, player_id: str, memory: Memory) -> float:
        relationship = (memory.get("relationships", {}) or {}).get(player_id, {}) or {}
        return float(relationship.get("hostility", 0.0) or 0.0)

    def _needs_food(self, player: dict) -> bool:
        if player.get("health") not in CARE_HEALTH_STATES:
            return False
        return self._food_count(player) <= 1.0

    def _food_need(self, player: dict) -> float:
        return max(0.0, 2.0 - self._food_count(player))

    def _needs_fire(self, player: dict, memory: Memory) -> bool:
        if player.get("health") not in CARE_HEALTH_STATES:
            return False
        if player.get("fire_status") != "COLD":
            return False
        if memory.get("fire_status") != "HOST":
            return False
        guests = memory.get("fire_guests", []) or []
        max_seats = int(memory.get("max_fire_seats", 0) or 0)
        return max_seats <= 0 or len(guests) < max_seats

    def _fire_need(self, player: dict) -> float:
        chance = float(player.get("sickness_chance", 0.0) or 0.0)
        return 1.0 + max(0.0, chance)

    def _food_count(self, player: dict) -> float:
        resources = player.get("resources", {}) or {}
        return float(resources.get("food", player.get("food", 0)) or 0)

    def _rank_targets(self, targets: list[str], vulnerabilities: dict[str, dict]) -> list[str]:
        return sorted(
            targets,
            key=lambda player_id: (
                vulnerabilities[player_id].get("trust", 0.0),
                vulnerabilities[player_id].get("complementarity", 0.0),
                vulnerabilities[player_id].get("needs_food", 0.0)
                + vulnerabilities[player_id].get("needs_fire", 0.0),
            ),
            reverse=True,
        )
