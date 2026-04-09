from typing import List, Dict, Optional
from pydantic import Field, BaseModel
from openenv.core.env_server.types import Action, Observation

class UnitAction(BaseModel):
    move: int = Field(..., description="0-7: Move directions (N, NE, E, SE, S, SW, W, NW), 8: Stay")
    act: bool = Field(default=False, description="True to perform specialized action (Tanker: Drop Water, Crew: Suppress)")

class WildfireAction(Action):
    actions: List[UnitAction] = Field(..., min_length=3, max_length=3, description="Actions for [Tanker, Crew1, Crew2]")

class UnitStatus(BaseModel):
    type: str = Field(..., description="tanker or ground_crew")
    pos: List[int] = Field(..., min_length=2, max_length=2, description="[row, col]")
    resource: float = Field(..., description="Water level for Tanker, Stamina for Crew")
    max_resource: float = Field(..., description="Maximum resource capacity")

class WildfireObservation(Observation):
    # Flattened grid data for easier model consumption, 
    # but also structured for human/debug readability
    fuel_grid: List[List[float]] = Field(..., description="20x20 fuel levels")
    fire_grid: List[List[float]] = Field(..., description="20x20 fire intensity")
    moisture_grid: List[List[float]] = Field(..., description="20x20 moisture levels")
    structure_grid: List[List[int]] = Field(..., description="20x20 structure locations (1=structure, 0=none)")
    
    units: List[UnitStatus] = Field(..., description="Status of all units")
    wind_dir: int = Field(..., description="0-7 wind direction")
    wind_speed: float = Field(..., description="Current wind speed")
    
    done: bool = Field(default=False)
    reward: float = Field(default=0.01)
    info: Dict = Field(default_factory=dict)
