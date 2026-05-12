DEVELOPMENT_COSTS = {
    "Farm": {
        "build": {"wood": 2},
        "maintain": {"wood": 2, "iron": 1},
        "upgrade": {"wood": 5, "iron": 2}
    },
    "Woods": {
        "build": {"food": 1, "wood": 1},
        "maintain": {"food": 2, "iron": 2},
        "upgrade": {"food": 5, "iron": 3}
    },
    "Mine": {
        "build": {"wood": 2, "food": 2},
        "maintain": {"wood": 3, "food": 3},
        "upgrade": {"wood": 2, "food": 2, "iron": 5}
    }
}

STARTING_INVENTORY = {
    "wood": 3,
    "food": 2,
    "iron": 1,
}

CAMPFIRE_COST = {"wood": 1}
MAX_FIRE_SEATS = 3

# seconds
PHASE_LENGTH = 120

GAME_LENGTH = 5