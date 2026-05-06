import random


def get_random_name():
    """
    Generates a random name for a new player.
    Extracted from Game class to keep the engine focused on mechanics.
    """
    # Replace this list with your actual name generation logic or file reading
    names = ["Brak", "Grom", "Thrall", "Krag", "Ruk", "Snaga", "Borg", "Zog"]
    return random.choice(names)
