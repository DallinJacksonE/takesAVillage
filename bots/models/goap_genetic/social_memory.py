from dataclasses import dataclass, field


RESOURCE_TYPES = ("food", "wood", "iron")
SUPPORT_REASONS = {"SICK_PARTNER_FOOD", "SUPPORT_GIFT", "CAMPFIRE_SUPPORT"}


def clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


@dataclass
class RelationshipSentiment:
    """Directional sentiment one bot holds about one counterparty."""

    trust: float = 0.0
    fairness: float = 0.0
    generosity: float = 0.0
    reciprocity: float = 0.0
    hostility: float = 0.0
    affinity: float = 0.0
    confidence: float = 0.0
    last_interaction_day: int | None = None

    def apply(self, evidence: "SocialEventEvidence", learning_rate: float,
              decay: float) -> None:
        self.trust = clamp((1.0 - decay) * self.trust + learning_rate * evidence.trust)
        self.fairness = clamp((1.0 - decay) * self.fairness + learning_rate * evidence.fairness)
        self.generosity = clamp((1.0 - decay) * self.generosity + learning_rate * evidence.generosity)
        self.reciprocity = clamp((1.0 - decay) * self.reciprocity + learning_rate * evidence.reciprocity)
        self.hostility = clamp(
            (1.0 - decay) * self.hostility + learning_rate * evidence.hostility,
            0.0,
            1.0,
        )
        self.affinity = clamp((1.0 - decay) * self.affinity + learning_rate * evidence.affinity)
        self.confidence = clamp(
            self.confidence + evidence.strength * 0.25,
            0.0,
            1.0,
        )
        if evidence.day is not None:
            self.last_interaction_day = evidence.day

    def as_dict(self) -> dict:
        return {
            "trust": self.trust,
            "fairness": self.fairness,
            "generosity": self.generosity,
            "reciprocity": self.reciprocity,
            "hostility": self.hostility,
            "affinity": self.affinity,
            "confidence": self.confidence,
            "last_interaction_day": self.last_interaction_day,
        }


@dataclass(frozen=True)
class SocialEventEvidence:
    """Normalized relationship evidence from one resolved exchange."""

    event_id: str
    counterparty_id: str
    kind: str
    trust: float = 0.0
    fairness: float = 0.0
    generosity: float = 0.0
    reciprocity: float = 0.0
    hostility: float = 0.0
    affinity: float = 0.0
    strength: float = 0.0
    day: int | None = None


class ExchangeClassifier:
    """Classifies resolved exchanges into sentiment evidence.

    Input events are from the observing bot's perspective: `actual_sent` is
    what I transferred; `actual_received` is what the counterparty transferred
    to me; `promised_received` is what I expected them to transfer.
    """

    def __init__(self, cheat_tolerance: float = 0.10,
                 gift_return_tolerance: float = 0.25):
        self.cheat_tolerance = cheat_tolerance
        self.gift_return_tolerance = gift_return_tolerance

    def classify(self, event: dict) -> SocialEventEvidence:
        event_id = str(event.get("id") or event.get("trade_id") or "")
        counterparty_id = str(event.get("counterparty_id") or event.get("target_id") or event.get("initiator_id") or "")
        reason = event.get("reason", "NORMAL_TRADE")
        promised_received = event.get("promised_received", {}) or {}
        actual_received = event.get("actual_received", {}) or {}
        actual_sent = event.get("actual_sent", {}) or {}
        day = event.get("day")

        promised_value = self._bundle_value(promised_received, event)
        received_value = self._bundle_value(actual_received, event)
        sent_value = self._bundle_value(actual_sent, event)

        if reason in SUPPORT_REASONS:
            return self._support_evidence(
                event_id,
                counterparty_id,
                promised_value,
                received_value,
                sent_value,
                day,
            )

        if promised_value > 0:
            shortfall_ratio = max(0.0, promised_value - received_value) / promised_value
            if shortfall_ratio > self.cheat_tolerance:
                if reason == "WAGE_PAYMENT":
                    return self._wage_cheat(event_id, counterparty_id, shortfall_ratio, day)
                return self._trade_cheat(event_id, counterparty_id, shortfall_ratio, day)
            if received_value <= promised_value:
                return SocialEventEvidence(
                    event_id=event_id,
                    counterparty_id=counterparty_id,
                    kind="fulfilled_exchange",
                    trust=0.10,
                    fairness=0.10,
                    affinity=0.03,
                    strength=0.25,
                    day=day,
                )

        surplus_value = max(0.0, received_value - max(promised_value, sent_value))
        if received_value > 0 and sent_value <= self.gift_return_tolerance * received_value:
            gift_strength = self._normalize(surplus_value or (received_value - sent_value))
            return SocialEventEvidence(
                event_id=event_id,
                counterparty_id=counterparty_id,
                kind="gift_received",
                trust=0.10 * gift_strength,
                fairness=0.05 * gift_strength,
                generosity=0.35 * gift_strength,
                reciprocity=-0.20 * gift_strength,
                affinity=0.25 * gift_strength,
                strength=gift_strength,
                day=day,
            )

        if sent_value > 0 and promised_value <= 0 and received_value <= self.gift_return_tolerance * sent_value:
            return self._support_evidence(
                event_id,
                counterparty_id,
                promised_value,
                received_value,
                sent_value,
                day,
            )

        return SocialEventEvidence(
            event_id=event_id,
            counterparty_id=counterparty_id,
            kind="neutral_exchange",
            day=day,
        )

    def _trade_cheat(self, event_id: str, counterparty_id: str,
                     shortfall_ratio: float, day: int | None) -> SocialEventEvidence:
        strength = self._normalize(shortfall_ratio)
        return SocialEventEvidence(
            event_id=event_id,
            counterparty_id=counterparty_id,
            kind="trade_cheated",
            trust=-0.40 * strength,
            fairness=-0.35 * strength,
            reciprocity=0.20 * strength,
            hostility=0.30 * strength,
            affinity=-0.25 * strength,
            strength=strength,
            day=day,
        )

    def _wage_cheat(self, event_id: str, counterparty_id: str,
                    shortfall_ratio: float, day: int | None) -> SocialEventEvidence:
        strength = self._normalize(shortfall_ratio)
        return SocialEventEvidence(
            event_id=event_id,
            counterparty_id=counterparty_id,
            kind="wage_cheated",
            trust=-0.60 * strength,
            fairness=-0.50 * strength,
            reciprocity=0.30 * strength,
            hostility=0.45 * strength,
            affinity=-0.35 * strength,
            strength=strength,
            day=day,
        )

    def _support_evidence(self, event_id: str, counterparty_id: str,
                          promised_value: float, received_value: float,
                          sent_value: float,
                          day: int | None) -> SocialEventEvidence:
        if received_value > 0.0 and sent_value <= self.gift_return_tolerance * received_value:
            strength = self._normalize(received_value)
            return SocialEventEvidence(
                event_id=event_id,
                counterparty_id=counterparty_id,
                kind="support_received",
                trust=0.15 * strength,
                generosity=0.40 * strength,
                reciprocity=-0.15 * strength,
                affinity=0.30 * strength,
                strength=strength,
                day=day,
            )
        if sent_value > 0.0 and received_value <= self.gift_return_tolerance * sent_value:
            strength = self._normalize(sent_value)
            return SocialEventEvidence(
                event_id=event_id,
                counterparty_id=counterparty_id,
                kind="support_given",
                trust=0.05 * strength,
                generosity=0.10 * strength,
                reciprocity=0.20 * strength,
                affinity=0.15 * strength,
                strength=strength,
                day=day,
            )
        if promised_value > 0.0:
            shortfall = max(0.0, promised_value - max(received_value, sent_value)) / promised_value
            strength = self._normalize(shortfall)
            return SocialEventEvidence(
                event_id=event_id,
                counterparty_id=counterparty_id,
                kind="support_failed",
                trust=-0.10 * strength,
                fairness=-0.10 * strength,
                hostility=0.05 * strength,
                affinity=-0.05 * strength,
                strength=strength,
                day=day,
            )
        return SocialEventEvidence(
            event_id=event_id,
            counterparty_id=counterparty_id,
            kind="support_neutral",
            day=day,
        )

    def _bundle_value(self, bundle: dict | None, event: dict) -> float:
        weights = event.get("resource_weights", {}) or {}
        return float(sum(
            float((bundle or {}).get(resource, 0) or 0)
            * float(weights.get(resource, 1.0) or 0.0)
            for resource in RESOURCE_TYPES
        ))

    def _normalize(self, value: float) -> float:
        return clamp(value, 0.0, 1.0)


@dataclass
class SocialMemory:
    """Persistent relationship memory for a single bot process."""

    learning_rate: float = 0.5
    decay: float = 0.02
    classifier: ExchangeClassifier = field(default_factory=ExchangeClassifier)
    relationships: dict[str, RelationshipSentiment] = field(default_factory=dict)
    observed_event_ids: set[str] = field(default_factory=set)

    def relationship(self, player_id: str) -> RelationshipSentiment:
        if player_id not in self.relationships:
            self.relationships[player_id] = RelationshipSentiment()
        return self.relationships[player_id]

    def observe_exchange(self, event: dict) -> bool:
        evidence = self.classifier.classify(event)
        if (not evidence.event_id or not evidence.counterparty_id
                or evidence.event_id in self.observed_event_ids):
            return False
        self.observed_event_ids.add(evidence.event_id)
        self.relationship(evidence.counterparty_id).apply(
            evidence,
            learning_rate=self.learning_rate,
            decay=self.decay,
        )
        return True

    def observe_trade_history(self, my_id: str, trade_history: list[dict]) -> None:
        for record in trade_history or []:
            counterparty_id = self._counterparty_for_record(my_id, record)
            if not counterparty_id:
                continue
            self.observe_exchange({
                "id": record.get("id"),
                "counterparty_id": counterparty_id,
                "reason": record.get("reason", "NORMAL_TRADE"),
                "promised_received": record.get("requested", {}),
                "actual_received": record.get("actual_received", {}),
                "actual_sent": record.get("actual_sent", {}),
                "day": record.get("day"),
            })

    def observe_game_state(self, game_state: dict) -> None:
        """Observe relationship evidence available in the bot state DTO.

        The service sends bots `me.actions`, `me.timeline`, and
        `me.trade_history` through `Player.to_dict()` in
        `service/game/serializers/state.py`. We prefer timeline
        `TRADE_RESOLVED` boxes for actual transfer amounts because those are
        the resolved, inventory-capped quantities. Contract records provide the
        promised bundles and counterparty ids.
        """
        me = game_state.get("me", {}) or {}
        my_id = me.get("id")
        if not my_id:
            return

        self.observe_trade_history(my_id, me.get("trade_history", []) or [])

        actions_by_id = {
            action.get("id"): action
            for action in me.get("actions", []) or []
            if action.get("id")
        }
        for event in me.get("timeline", []) or []:
            if event.get("type") in {"JOINED_FIRE", "SEATED_GUEST"}:
                self.observe_campfire_event(my_id, event, game_state.get("day"))
                continue
            if event.get("type") != "TRADE_RESOLVED":
                continue
            data = event.get("data", {}) or {}
            trade_id = data.get("trade_id")
            contract = actions_by_id.get(trade_id, {})
            counterparty_id = self._counterparty_for_record(my_id, contract)
            if not counterparty_id:
                continue
            self.observe_exchange({
                "id": event.get("id") or trade_id,
                "counterparty_id": counterparty_id,
                "reason": contract.get("reason", "NORMAL_TRADE"),
                "promised_received": self._promised_received_for_contract(
                    my_id, contract),
                "actual_received": data.get("received", {}),
                "actual_sent": data.get("sent", {}),
                "day": game_state.get("day"),
            })

    def observe_campfire_event(self, my_id: str, event: dict,
                               day: int | None) -> None:
        data = event.get("data", {}) or {}
        event_id = str(event.get("id") or "")
        if event.get("type") == "JOINED_FIRE":
            host_id = data.get("host")
            if host_id and host_id != my_id:
                self._apply_campfire_evidence(SocialEventEvidence(
                    event_id=f"campfire:joined:{event_id or day}:{host_id}",
                    counterparty_id=host_id,
                    kind="campfire_support_received",
                    trust=0.15,
                    generosity=0.25,
                    reciprocity=-0.10,
                    affinity=0.25,
                    strength=0.75,
                    day=day,
                ))
        elif event.get("type") == "SEATED_GUEST":
            guest_id = data.get("guest")
            if guest_id and guest_id != my_id:
                self._apply_campfire_evidence(SocialEventEvidence(
                    event_id=f"campfire:seated:{event_id or day}:{guest_id}",
                    counterparty_id=guest_id,
                    kind="campfire_support_given",
                    generosity=0.05,
                    reciprocity=0.15,
                    affinity=0.10,
                    strength=0.5,
                    day=day,
                ))

    def _apply_campfire_evidence(self, evidence: SocialEventEvidence) -> None:
        if (not evidence.event_id or not evidence.counterparty_id
                or evidence.event_id in self.observed_event_ids):
            return
        self.observed_event_ids.add(evidence.event_id)
        self.relationship(evidence.counterparty_id).apply(
            evidence,
            learning_rate=self.learning_rate,
            decay=self.decay,
        )

    def as_memory(self) -> dict[str, dict]:
        return {
            player_id: relationship.as_dict()
            for player_id, relationship in self.relationships.items()
        }

    def _counterparty_for_record(self, my_id: str, record: dict) -> str | None:
        initiator_id = record.get("initiator_id")
        target_id = record.get("target_id")
        if initiator_id == my_id:
            return target_id
        if target_id == my_id:
            return initiator_id
        return target_id or initiator_id

    def _promised_received_for_contract(self, my_id: str, contract: dict) -> dict:
        if contract.get("type") != "TRADE":
            return contract.get("requested", {}) or {}
        if contract.get("initiator_id") == my_id:
            return contract.get("request_items", {}) or {}
        return contract.get("offer_items", {}) or {}
