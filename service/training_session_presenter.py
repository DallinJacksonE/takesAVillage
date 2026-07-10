def build_training_session_payload(active_training_sessions: dict) -> dict:
    sessions = []

    for session_id, session in active_training_sessions.items():
        sessions.append({
            "session_id": session_id,
            "current_game_id": session.get("current_game_id"),
            "ruleset": session.get("ruleset"),
            "bot_count": session.get("bot_count"),
            "generation": session.get("generation"),
            "generations_left": session.get("generations_left"),
            "games_per_generation": session.get("games_per_generation"),
            "games_completed": session.get("games_completed", 0),
            "games_failed": session.get("games_failed", 0),
            "current_generation_game_index": session.get("current_generation_game_index", 0),
            "population_size": len(session.get("population", [])),
            "elite_count": session.get("elite_count"),
            "selection_size": session.get("selection_size"),
            "mutation_strength": session.get("mutation_strength"),
            "mutation_rate": session.get("mutation_rate"),
            "random_immigrant_count": session.get("random_immigrant_count"),
            "generation_statistics": session.get("generation_statistics", [])
        })

    return {"sessions": sessions}
