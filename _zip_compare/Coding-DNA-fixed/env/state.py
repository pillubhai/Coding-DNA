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

        # Place structures — spread them across the grid for visibility
        num_s = diff_conf["num_structures"]
        s_placed = 0
        attempts = 0
        while s_placed < num_s and attempts < 500:
            # Spread structures: use grid-based placement
            row_block = random.randint(2, self.size - 4)
            col_block = random.randint(2, self.size - 4)
            r = row_block + random.randint(-2, 2)
            c = col_block + random.randint(-2, 2)
            r = max(1, min(self.size - 2, r))
            c = max(1, min(self.size - 2, c))
            if self.structures[r, c] == 0:
                # Ensure no structure within 2 cells of another
                nearby = np.sum(self.structures[max(0,r-2):r+3, max(0,c-2):c+3])
                if nearby == 0:
                    self.structures[r, c] = 1
                    self.fuel[r, c] = 0.5  # Some fuel at structures
                    s_placed += 1
            attempts += 1

        # Initial fires — start with MULTIPLE visible fire clusters
        # Place 3-6 fire sources, some near structures for urgency
        struct_coords = np.argwhere(self.structures == 1)
        fire_points = 0
        target_fires = max(3, num_s // 2)  # More fires for more structures

        # Half of fires near structures (dramatic tension)
        for _ in range(target_fires // 2):
            if len(struct_coords) > 0:
                sr, sc = struct_coords[random.randint(0, len(struct_coords) - 1)]
                # Start fire 1-3 cells away from a structure
                for attempt in range(20):
                    fr = sr + random.randint(-3, 3)
                    fc = sc + random.randint(-3, 3)
                    if 0 <= fr < self.size and 0 <= fc < self.size and self.fuel[fr, fc] > 0.15:
                        if self.fire[fr, fc] == 0:
                            self.fire[fr, fc] = 1.0
                            # Spread to 1-2 neighbors for initial cluster
                            for _ in range(random.randint(1, 2)):
                                nr = fr + random.randint(-1, 1)
                                nc = fc + random.randint(-1, 1)
                                if 0 <= nr < self.size and 0 <= nc < self.size and self.fuel[nr, nc] > 0.15:
                                    self.fire[nr, nc] = 0.8
                            fire_points += 1
                            break

        # Remaining fires at random locations
        while fire_points < target_fires:
            r, c = random.randint(0, self.size-1), random.randint(0, self.size-1)
            if self.fuel[r, c] > 0.15 and self.fire[r, c] == 0:
                self.fire[r, c] = 1.0
                # Make a small cluster
                for _ in range(random.randint(0, 2)):
                    nr = r + random.randint(-1, 1)
                    nc = c + random.randint(-1, 1)
                    if 0 <= nr < self.size and 0 <= nc < self.size and self.fuel[nr, nc] > 0.15:
                        self.fire[nr, nc] = 0.8
                fire_points += 1
        
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
