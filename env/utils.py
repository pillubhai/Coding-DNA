import numpy as np
import random
from typing import Dict, List, Tuple
try:
    from env.config import Config
except (ImportError, ValueError):
    from .config import Config

class FireDynamics:
    # Directions for 8-neighbor adjacency (N, NE, E, SE, S, SW, W, NW)
    ADJACENCY = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    
    @staticmethod
    def update_spread(state, ignition_prob: float):
        """
        Advance fire spread by one step across the grid.
        """
        new_fire = state.fire.copy()
        size = state.size
        
        # Identify current fire sources
        fire_indices = np.argwhere(state.fire > 0.1)
        
        for r, c in fire_indices:
            # Consume fuel at current location
            intensity = state.fire[r, c]
            state.fuel[r, c] = max(0, state.fuel[r, c] - 0.05 * intensity)
            
            # If fuel exhausted, fire dies out
            if state.fuel[r, c] <= 0:
                new_fire[r, c] = 0
                continue

            # Spread to neighbors
            for i, (dr, dc) in enumerate(FireDynamics.ADJACENCY):
                nr, nc = r + dr, c + dc
                
                if 0 <= nr < size and 0 <= nc < size:
                    # Skip if already burning or NO fuel
                    if state.fire[nr, nc] > 0.1 or state.fuel[nr, nc] <= 0.05:
                        continue
                    
                    # Calculate spread probability
                    # Base prob * fuel_level * (1 - moisture)
                    prob = ignition_prob * state.fuel[nr, nc] * (1.0 - state.moisture[nr, nc])
                    
                    # Wind influence: If neighbor matches wind direction, increase chance
                    if i == state.wind_dir:
                        prob *= (1.0 + 0.5 * state.wind_speed)
                    elif (i + 4) % 8 == state.wind_dir: # Counter-wind
                        prob *= 0.5
                    
                    if random.random() < prob:
                        new_fire[nr, nc] = 0.5 # Start as medium fire
        
        # Gradually increase fire intensity where fuel is plenty
        growing_mask = (new_fire > 0) & (state.fuel > 0.3)
        new_fire[growing_mask] = np.minimum(1.0, new_fire[growing_mask] + 0.05)
        
        return new_fire

    @staticmethod
    def apply_spot_fire(state, spot_fire_prob: float):
        """
        Occasional long-range sparks that jump downwind.
        """
        high_intensity_fires = np.argwhere(state.fire > 0.8)
        if len(high_intensity_fires) == 0:
            return state.fire
            
        if random.random() < spot_fire_prob:
            # Pick a source fire
            r, c = random.choice(high_intensity_fires)
            
            # Jump 3-5 cells downwind
            dr, dc = FireDynamics.ADJACENCY[state.wind_dir]
            jump = random.randint(3, 5)
            nr, nc = r + dr*jump, c + dc*jump
            
            if 0 <= nr < state.size and 0 <= nc < state.size:
                if state.fuel[nr, nc] > 0.2:
                    state.fire[nr, nc] = 0.5
        
        return state.fire

    @staticmethod
    def process_actions(state, actions: List):
        """
        Process move/act commands for Tanker and 2 Crews.
        """
        # actions is [tanker_act, crew1_act, crew2_act]
        for i, act in enumerate(actions):
            unit = state.agents[i]
            
            # Movement
            if 0 <= act.move <= 7:
                dr, dc = FireDynamics.ADJACENCY[act.move]
                nr, nc = unit["pos"][0] + dr, unit["pos"][1] + dc
                if 0 <= nr < state.size and 0 <= nc < state.size:
                    unit["pos"] = [nr, nc]
                    # Movement cost
                    cost = 2.0 if unit["type"] == "ground_crew" else 0.5
                    unit["resource"] = max(0, unit["resource"] - cost)
            
            # Acts
            if act.act and unit["resource"] > 0:
                r, c = unit["pos"]
                if unit["type"] == "tanker":
                    # Dropping water (3x3 area)
                    for dr in range(-1, 2):
                        for dc in range(-1, 2):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < state.size and 0 <= nc < state.size:
                                state.moisture[nr, nc] = min(1.0, state.moisture[nr, nc] + Config.WATER_DROP_EFFECT)
                    unit["resource"] -= 2.0
                else:
                    # Ground crew suppression (1x1 area, reduces intensity)
                    state.fire[r, c] = max(0, state.fire[r, c] - Config.SUPPRESSION_EFFECT)
                    unit["resource"] -= 5.0
                    
            # Resource Refill (only at corner bases: [0,0], [size-1,0], [0,size-1])
            r, c = unit["pos"]
            size = state.size
            at_base = (r == 0 and c == 0) or (r == size-1 and c == 0) or (r == 0 and c == size-1)
            if at_base:
                rate = Config.TANKER_REFILL_RATE if unit["type"] == "tanker" else Config.CREW_REFILL_RATE
                max_res = Config.TANKER_CAPACITY if unit["type"] == "tanker" else Config.CREW_STAMINA
                unit["resource"] = min(max_res, unit["resource"] + rate)
