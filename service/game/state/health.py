"""Pure player health state transitions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthTransition:
    health: str
    sickness_chance: float


def next_sickness_chance(sickness_chance, ate, warm, sickness_rules):
    chance = sickness_chance
    if chance is None:
        chance = sickness_rules["default"]
    if not ate:
        chance += sickness_rules["hunger_increase"]
    if not warm:
        chance += sickness_rules["cold_increase"]
    if ate and warm:
        chance = max(
            sickness_rules["default"],
            chance - sickness_rules["recovery"],
        )
    return chance


def transition_health(health, sickness_chance, ate, warm, check, sickness_rules):
    if health == "dead":
        chance = (
            sickness_rules["default"]
            if sickness_chance is None
            else sickness_chance
        )
        return HealthTransition("dead", chance)

    chance = next_sickness_chance(sickness_chance, ate, warm, sickness_rules)

    if ate and warm:
        if health == "sick":
            return HealthTransition("recovering", chance)
        if health == "recovering":
            return HealthTransition("healthy", sickness_rules["default"])

    if check < chance:
        if health == "sick":
            return HealthTransition("dead", chance)
        return HealthTransition("sick", chance)

    return HealthTransition(health, chance)
