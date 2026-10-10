from pydantic import BaseModel


class TrainingRequest(BaseModel):
    ruleset: str = "default"
    botCount: int = 5
    generations: int = 1
    baseGenome: str = "random"
    botModel: str = "genetic"
    mutationStrength: float = 0.25
    mutationRate: float = 0.15
    randomImmigrantCount: int = 1
    gamesPerGeneration: int = 5


class CancelTrainingRequest(BaseModel):
    reason: str = "Training cancelled by operator"
