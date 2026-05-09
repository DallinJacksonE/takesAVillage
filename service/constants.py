# constants.py
DEVELOPMENT_COSTS = {
    "Farm": {
        "build": {"wood": 10},
        "maintain": {"wood": 2},
        "upgrade": {"wood": 15, "iron": 5}
    },
    "Woods": {
        "build": {"food": 10},
        "maintain": {"food": 2},
        "upgrade": {"food": 15, "iron": 5}
    },
    "Mine": {
        "build": {"wood": 15, "food": 15},
        "maintain": {"wood": 3, "food": 3},
        "upgrade": {"wood": 20, "food": 20, "iron": 10}
    }
}

CAMPFIRE_COST = {"wood": 1}
MAX_FIRE_SEATS = 3
