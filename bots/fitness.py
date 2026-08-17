from dataclasses import dataclass
from statistics import mean


RESOURCE_TYPES = ("food", "wood", "iron")


@dataclass(frozen=True)
class FitnessReport:
    """Explainable fitness result used by training and debugging."""
    score: float
    components: dict[str, float]
    stats: dict


def calculate_fitness(game_state: dict) -> float:
    """
    Scores a bot episode for genetic training.

    Survival remains dominant, but village-specific outcomes now contribute
    explainable secondary objectives so GOAP genomes can evolve toward richer
    play instead of only hoarding resources or ending phases.
    """
    return calculate_fitness_report(game_state).score


def calculate_fitness_report(game_state: dict) -> FitnessReport:
    stats = collect_episode_stats(game_state)
    components = {
        "survival": _survival_score(stats),
        "resources": stats["resource_total"] * 2.0,
        "developments_owned": stats["developments_owned"] * 25.0,
        "development_levels": stats["development_levels"] * 10.0,
        "maintenance": stats["maintenance_days"] * 3.0,
        "production": stats["production_generated"] * 4.0,
        "successful_work": stats["successful_work_count"] * 20.0,
        "profitable_trades": stats["profitable_trade_value"] * 8.0,
        "fulfilled_contracts": stats["fulfilled_contract_count"] * 15.0,
        "campfire_cooperation": stats["campfire_cooperation_count"] * 12.0,
        "contest_outcomes": stats["contest_success_count"] * 10.0,
        "relative_ranking": stats["relative_rank_score"] * 50.0,
        "behavior_penalty": _behavior_penalty(stats),
    }
    return FitnessReport(
        score=float(sum(components.values())),
        components=components,
        stats=stats,
    )


def collect_episode_stats(game_state: dict) -> dict:
    me = game_state.get("me", {})
    my_id = me.get("id")
    resources = _resource_bundle(me.get("resources", {}))
    timeline = me.get("timeline", []) or []
    developments = _owned_developments(game_state, me)
    trade_history = me.get("trade_history", []) or []
    actions = me.get("actions", []) or []

    stats = {
        "bot_id": my_id,
        "day": max(0, int(game_state.get("day", 0) or 0)),
        "game_length": max(0, int(game_state.get("game_length", 0) or 0)),
        "survived": me.get("health") != "dead",
        "health": me.get("health"),
        "resources": resources,
        "resource_total": sum(resources.values()),
        "developments_owned": len(developments),
        "development_levels": sum(int(dev.get("level", 1) or 1) for dev in developments),
        "maintenance_days": sum(max(0, int(dev.get("maintenance_days", 0) or 0)) for dev in developments),
        "production_generated": _production_generated(timeline),
        "successful_work_count": _count_action(timeline, "COMMIT_WORK"),
        "profitable_trade_value": _profitable_trade_value(trade_history, timeline),
        "fulfilled_contract_count": _fulfilled_contract_count(actions, timeline),
        "campfire_cooperation_count": _campfire_cooperation_count(timeline),
        "contest_success_count": _contest_success_count(timeline),
        "illegal_action_count": _count_event_type(timeline, "ILLEGAL_ACTION"),
        "no_op_count": _count_event_type(timeline, "NO_OP"),
        "finish_phase_count": _count_action(timeline, "FINISH_PHASE"),
        "relative_rank_score": _relative_rank_score(game_state, me),
    }
    stats["fitness_inputs"] = dict(stats)
    return stats


def _survival_score(stats: dict) -> float:
    days_survived = stats["day"]
    game_length = max(days_survived, stats["game_length"])
    score = days_survived * 100.0
    if stats["survived"]:
        score += (19 - days_survived) * 100.0 + 200
    return score


def _behavior_penalty(stats: dict) -> float:
    repeated_finish_count = max(0, stats["finish_phase_count"] - 1)
    return -float(
        stats["illegal_action_count"] * 50.0
        + stats["no_op_count"] * 20.0
        + repeated_finish_count * 5.0
    )


def _resource_bundle(raw: dict | None) -> dict[str, int]:
    raw = raw or {}
    return {resource: int(raw.get(resource, 0) or 0) for resource in RESOURCE_TYPES}


def _owned_developments(game_state: dict, me: dict) -> list[dict]:
    my_id = me.get("id")
    owned_ids = set(me.get("developments", []) or [])
    return [
        dev for dev in game_state.get("developments", []) or []
        if dev.get("owner_id") == my_id or dev.get("id") in owned_ids
    ]


def _events(timeline: list[dict], event_type: str | None = None):
    for event in timeline:
        if event_type is None or event.get("type") == event_type:
            yield event


def _event_action(event: dict) -> str | None:
    data = event.get("data", {}) or {}
    return data.get("action") or data.get("Action")


def _count_event_type(timeline: list[dict], event_type: str) -> int:
    return sum(1 for _event in _events(timeline, event_type))


def _count_action(timeline: list[dict], action_name: str) -> int:
    return sum(
        1 for event in _events(timeline)
        if _event_action(event) == action_name
    )


def _production_generated(timeline: list[dict]) -> float:
    total = 0.0
    for event in _events(timeline, "LABOR_EXPLOITED"):
        total += float((event.get("data", {}) or {}).get("yield", 0) or 0)
    return total


def _profitable_trade_value(trade_history: list[dict], timeline: list[dict]) -> float:
    trade_values = [_trade_record_value(record) for record in trade_history]
    for event in _events(timeline, "TRADE_RESOLVED"):
        data = event.get("data", {}) or {}
        trade_values.append(_bundle_total(data.get("received")) - _bundle_total(data.get("sent")))
    return sum(value for value in trade_values if value > 0)


def _trade_record_value(record: dict) -> float:
    received = record.get("actual_received", record.get("received", {}))
    sent = record.get("actual_sent", record.get("sent", {}))
    return _bundle_total(received) - _bundle_total(sent)


def _bundle_total(bundle: dict | None) -> float:
    return float(sum((bundle or {}).values()))


def _fulfilled_contract_count(actions: list[dict], timeline: list[dict]) -> int:
    completed_actions = sum(
        1 for action in actions
        if action.get("status") == "FINALIZED"
    )
    finalized_events = sum(
        1 for event in _events(timeline, "ACTION_UPDATED_FINALIZED")
        if (event.get("data", {}) or {}).get("type") in {"TRADE", "EMPLOYMENT"}
    )
    return completed_actions + finalized_events


def _campfire_cooperation_count(timeline: list[dict]) -> int:
    return (
        _count_event_type(timeline, "JOINED_FIRE")
        + _count_event_type(timeline, "SEATED_GUEST")
    )


def _contest_success_count(timeline: list[dict]) -> int:
    return (
        _count_action(timeline, "CONTEST")
        + _count_action(timeline, "CONTEST_SCHEDULED")
    )


def _relative_rank_score(game_state: dict, me: dict) -> float:
    players = game_state.get("player_list", []) or []
    my_id = me.get("id")
    if not players or not my_id:
        return 0.0

    scores = []
    for player in players:
        resource_total = sum(_resource_bundle(player.get("resources", {})).values())
        dev_count = len(player.get("developments", []) or [])
        alive_bonus = 1 if player.get("health") != "dead" else 0
        scores.append((player.get("id"), resource_total + dev_count * 3 + alive_bonus * 5))

    my_score = next((score for player_id, score in scores if player_id == my_id), None)
    if my_score is None:
        return 0.0
    if len(scores) == 1:
        return 1.0

    lower_count = sum(1 for _player_id, score in scores if score < my_score)
    tied_count = sum(1 for _player_id, score in scores if score == my_score) - 1
    return (lower_count + tied_count * 0.5) / (len(scores) - 1)


def average(values: list[float]) -> float:
    return mean(values) if values else 0.0
