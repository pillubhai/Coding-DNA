class Config:
    GRID_SIZE = 20
    MAX_STEPS = 1000
    
    # Unit Config
    TANKER_CAPACITY = 10.0
    TANKER_REFILL_RATE = 1.0
    CREW_STAMINA = 100.0
    CREW_REFILL_RATE = 5.0
    
    # Damage/Effect Config
    WATER_DROP_EFFECT = 0.5  # Moisture reduction
    SUPPRESSION_EFFECT = 0.2 # Fire intensity reduction
    
    # Difficulty Modes
    EASY = {
        "ignition_prob": 0.05,
        "wind_volatility": 0.01,
        "fuel_density": 0.6,
        "spot_fire_prob": 0.01,
        "num_structures": 5
    }
    
    MEDIUM = {
        "ignition_prob": 0.12,
        "wind_volatility": 0.05,
        "fuel_density": 0.75,
        "spot_fire_prob": 0.05,
        "num_structures": 10
    }
    
    HARD = {
        "ignition_prob": 0.20,
        "wind_volatility": 0.15,
        "fuel_density": 0.9,
        "spot_fire_prob": 0.15,
        "num_structures": 20
    }
