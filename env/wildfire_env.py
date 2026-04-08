import random
from uuid import uuid4
from typing import Dict, List, Optional
import numpy as np

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from models import WildfireAction, WildfireObservation, UnitStatus
    from env.state import WildfireState
    from env.utils import FireDynamics
    from env.config import Config
except (ImportError, ValueError):
    from ..models import WildfireAction, WildfireObservation, UnitStatus
    from .state import WildfireState
    from .utils import FireDynamics
    from .config import Config

class WildfireEnv(Environment):
    """
    WildfireContainment-v0: An environment for agentic wildfire suppression.
    """
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self, difficulty: str = "medium"):
        self.difficulty = difficulty
        self._env_state = WildfireState(difficulty=difficulty)
        self._state = State(episode_id=str(uuid4()), step_count=0)

    def reset(self, seed: Optional[int] = None) -> WildfireObservation:
        """
        Reset the environment state and episode trackers.
        """
        self._env_state.reset(seed=seed)
        self._env_state.total_reward = 0.0
        self._state = State(episode_id=str(uuid4()), step_count=0)

        return self._get_observation(reward=0.0, done=False)

    def step(self, action: WildfireAction) -> WildfireObservation: # type: ignore
        """
        Execute one step of the simulation.
        """
        self._state.step_count += 1
        self._env_state.total_reward = getattr(self._env_state, 'total_reward', 0.0)

        # 1. Process agent actions (movement, drops)
        FireDynamics.process_actions(self._env_state, action.actions)

        # 2. Get current fire count and structure count for reward baseline
        old_fire_sum = np.sum(self._env_state.fire)
        old_structures = np.sum(self._env_state.structures)

        # 3. Update fire spread and spot fires
        diff_conf = getattr(Config, self.difficulty.upper())
        self._env_state.fire = FireDynamics.update_spread(self._env_state, diff_conf["ignition_prob"])
        self._env_state.fire = FireDynamics.apply_spot_fire(self._env_state, diff_conf["spot_fire_prob"])

        # 4. Check for structure loss (fire intensity > 0.5 consumes structure)
        structure_mask = (self._env_state.fire > 0.5) & (self._env_state.structures == 1)
        self._env_state.structures[structure_mask] = 0

        # 5. Calculate Reward
        current_fire_sum = np.sum(self._env_state.fire)
        current_structures = np.sum(self._env_state.structures)

        # Fire reduction reward
        reward = (old_fire_sum - current_fire_sum) * 0.1
        # Structure loss penalty
        reward -= (old_structures - current_structures) * 5.0
        # Survival bonus
        reward += (current_structures * 0.01)

        # 6. Check Done
        done = False
        if self._state.step_count >= Config.MAX_STEPS:
            done = True
        if current_fire_sum <= 0:
            reward += 10.0 # Containment bonus
            done = True
        if current_structures <= 0:
            reward -= 10.0 # Total loss penalty
            done = True

        self._env_state.total_reward += reward
        return self._get_observation(reward=reward, done=done)

    def _get_observation(self, reward: float, done: bool) -> WildfireObservation:
        """
        Construct the Observation object from internal state.
        """
        grid_data = self._env_state.get_observation_arrays()
        
        unit_statuses = []
        for agent in self._env_state.agents:
            unit_statuses.append(UnitStatus(
                type=agent["type"],
                pos=agent["pos"],
                resource=float(agent["resource"]),
                max_resource=Config.TANKER_CAPACITY if agent["type"] == "tanker" else Config.CREW_STAMINA
            ))
            
        return WildfireObservation(
            fuel_grid=grid_data["fuel"],
            fire_grid=grid_data["fire"],
            moisture_grid=grid_data["moisture"],
            structure_grid=grid_data["structures"],
            units=unit_statuses,
            wind_dir=self._env_state.wind_dir,
            wind_speed=self._env_state.wind_speed,
            done=done,
            reward=reward,
            info={
                "step": self._state.step_count,
                "episode_id": self._state.episode_id,
                "difficulty": self.difficulty
            }
        )

    @property
    def state(self) -> State:
        return self._state

    def get_state(self) -> dict:
        """
        Full environment snapshot for serialization, debugging, and replay.
        Required by OpenEnv spec.
        """
        diff_conf = getattr(Config, self.difficulty.upper())
        fire_cells = int(np.sum(self._env_state.fire > 0.1))
        struct_remaining = int(np.sum(self._env_state.structures))
        return {
            "episode_id": self._state.episode_id,
            "step": int(self._state.step_count),
            "difficulty": self.difficulty,
            "grid_size": int(Config.GRID_SIZE),
            "max_steps": int(Config.MAX_STEPS),
            "wind_dir": int(self._env_state.wind_dir),
            "wind_speed": float(self._env_state.wind_speed),
            "agents": [
                {
                    "type": a["type"],
                    "pos": [int(a["pos"][0]), int(a["pos"][1])],
                    "resource": float(a["resource"])
                }
                for a in self._env_state.agents
            ],
            "fire_cells": fire_cells,
            "structures_remaining": struct_remaining,
            "initial_structures": int(diff_conf["num_structures"]),
            "terminated": bool(fire_cells == 0),
            "cumulative_reward": float(getattr(self._env_state, "total_reward", 0.0)),
        }
