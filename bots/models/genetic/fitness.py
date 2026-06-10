def calculate_fitness(game_state: dict) -> float:
    """
    Evaluates the final game state and returns a fitness score.
    As this logic grows, you can easily inject different scoring
    strategies here.
    """
    me = game_state.get("me", {})

    # Extract baseline stats
    resources = me.get("resources", {"wood": 0, "food": 0, "iron": 0})
    is_alive = me.get("health") != "dead"

    # Calculate base score
    score = (
        resources.get("food", 0) +
        resources.get("wood", 0) +
        resources.get("iron", 0) +
        (50 if is_alive else 0)
    )

    days_survived = game_state.get("day", 0)

    score += 10 * days_survived # Reward for lasting longer in the game

    # As you add more complex metrics (e.g., developments owned,
    # kill count, etc.),
    # simply extract them from game_state and weigh them here.

    return float(score)
