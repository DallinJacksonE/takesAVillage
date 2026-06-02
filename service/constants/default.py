DEVELOPMENT_COSTS = {
    # CURRENTLY USES ONLY THE BUILD INFORMATION SINCE UPGRADE
    # AND MAINTENANCE COSTS ARE COMPUTED DYNAMICALLY IN developments.py
    # USING get_maintenance_cost AND get_upgrade_cost
    "Farm": {
        "build": {"wood": 2},
        "maintain": {"wood": 2, "iron": 1},
        "upgrade": {"wood": 5, "iron": 2}
    },
    "Woods": {
        "build": {"food": 1, "wood": 1},
        "maintain": {"food": 2, "iron": 1},
        "upgrade": {"food": 5, "iron": 2}
    },
    "Mine": {
        "build": {"wood": 2, "food": 2},
        "maintain": {"wood": 3, "food": 3},
        "upgrade": {"wood": 2, "food": 2, "iron": 5}
    }
}


MAX_DEVELOPMENT_LEVEL = 3
MAINTENANCE_DAYS = 7

STARTING_INVENTORY = {
    "wood": 3,
    "food": 2,
    "iron": 1,
}

CAMPFIRE_COST = {"wood": 1}
MAX_FIRE_SEATS = 3

# seconds
PHASE_LENGTH = 120

GAME_LENGTH = 15

AVAILABLE_NAMES = ["Bork", "Torq", "Loki", "Snort", "Smoky", "Larry", "Ig",
                   "Irates", "Kranak", "Areril",
                   "Keenmaw", "Lerk", "Brarx", "Krateges", "Krazz", "Gliregg",
                   "Tresagg", "Meemigg", "Nemarx", "Faril", "Stusz"]
DEFAULT_SICKNESS = .03

HUNGER_SICKNESS_INCREASE = .2

COLD_SICKNESS_INCREASE = .1

RECOVERY_RATE = .07  # Rate for sickness chance going down

# Tiles per player, min of 1 logic handled in map factory
FARMS_RATIO = 1/2

WOODS_RATIO = .75

MOUNTAINS_RATIO = 2/5
