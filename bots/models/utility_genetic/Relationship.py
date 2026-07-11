
from dataclasses import dataclass


@dataclass
class Relationship:
    trust: float         # Will they honor agreements?
    generosity: float    # Do they help others?
    friendship: float    # Positive interactions
    greed: float         # Takes more than gives