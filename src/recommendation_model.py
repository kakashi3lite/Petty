from dataclasses import dataclass, field

import numpy as np


@dataclass
class PetProfile:
    age: float
    weight: float
    activity_level: int
    species: str
    breed: str = field(default="unknown")
    body_condition_score: float = field(default=5.0)
    life_stage: str = field(default="adult")
    activity_description: str = field(default="typical")

    def to_vector(self) -> np.ndarray:
        return np.array([self.age, self.weight, self.activity_level, self.body_condition_score], dtype=float)
