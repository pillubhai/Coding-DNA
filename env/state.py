import numpy as np
import random
from typing import Dict, List, Tuple
try:
    from env.config import Config
except (ImportError, ValueError):
    from .config import Config

class WildfireState:
    def __init__(self, difficulty: str = "medium", seed: int = None):
        self.size = Config.GRID_SIZE
        self.difficulty = difficulty
        self.seed = seed
        self.reset(seed)

    def reset(self, seed: int = None):
        if seed is not None:
            self.seed = seed
            random.seed(seed)
            np.random.seed(seed)
        
        # Grid initialization
        # 0: Fuel, 1: Fire, 2: Moisture, 3: Structures
        self.fuel = np.zeros((self.size, self.size), dtype=np.float32)
        self.fire = np.zeros((self.size, self.size), dtype=np.float32)
        self.moisture = np.zeros((self.size, self.size), dtype=np.float32)
        self.structures = np.zeros((self.size, self.size), dtype=np.int8)
        
        # Difficulty config
        diff_conf = getattr(Config, self.difficulty.upper())
        
        # Random fuel distribution
        self.fuel = np.random.uniform(0.1, 1.0, (self.size, self.size)).astype(np.float32)
        # Apply fuel density mask
        mask = np.random.random((self.size, self.size)) < diff_conf["fuel_density"]
        self.fuel *= mask
        
        # Place structures
        num_s = diff_conf["num_structures"]
        s_placed = 0
        while s_placed < num_s:
            r, c = random.randint(0, self.size-1), random.randint(0, self.size-1)
            if self.structures[r, c] == 0:
                self.structures[r, c] = 1
                self.fuel[r, c] = 0.5 # Some fuel in structures
                s_placed += 1
        
        # Initial fires (random 1-2 points)
        for _ in range(random.randint(1, 2)):
            r, c = random.randint(0, self.size-1), random.randint(0, self.size-1)
            if self.fuel[r, c] > 0.2:
                self.fire[r, c] = 1.0
        
        # Agents [Tanker, Crew1, Crew2]
        self.agents = [
            {"type": "tanker", "pos": [0, 0], "resource": Config.TANKER_CAPACITY},
            {"type": "ground_crew", "pos": [self.size-1, 0], "resource": Config.CREW_STAMINA},
            {"type": "ground_crew", "pos": [0, self.size-1], "resource": Config.CREW_STAMINA},
        ]
        
        # Environmental dynamics
        self.wind_dir = random.randint(0, 7)
        self.wind_speed = random.uniform(0.5, 2.0)
        self.step_count = 0
        self.total_reward = 0.0

    def get_observation_arrays(self):
        return {
            "fuel": self.fuel.tolist(),
            "fire": self.fire.tolist(),
            "moisture": self.moisture.tolist(),
            "structures": self.structures.tolist()
        }
