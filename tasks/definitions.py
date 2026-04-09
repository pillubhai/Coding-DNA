# tasks/definitions.py
# Synthetic wildfire tasks for grading and validation.

TASKS = {
    "easy": {
        "description": "Low ignition wildfire with few structures and slow wind.",
        "ideal_action": "contain",
        "steps": [
            {
                "observation": (
                    "Wildfire Report — Sector A:\n"
                    "Fire clusters are small and isolated.\n"
                    "Structures remaining: 5\n"
                    "Wind speed: low\n"
                    "Decision: contain, suppress, or protect."
                ),
                "signals": {
                    "fire_pressure": 0.22,
                    "structure_risk": 0.18,
                    "resource_pressure": 0.12,
                    "ideal_action": "contain",
                },
            }
        ],
    },
    "medium": {
        "description": "Moderate wildfire spread with variable wind and limited time.",
        "ideal_action": "suppress",
        "steps": [
            {
                "observation": (
                    "Wildfire Report — Sector B:\n"
                    "Fire is advancing toward structures.\n"
                    "Structures remaining: 10\n"
                    "Wind speed: medium\n"
                    "Decision: contain, suppress, or protect."
                ),
                "signals": {
                    "fire_pressure": 0.56,
                    "structure_risk": 0.48,
                    "resource_pressure": 0.33,
                    "ideal_action": "suppress",
                },
            }
        ],
    },
    "hard": {
        "description": "Intense wildfire spread with frequent spot fires and high structure exposure.",
        "ideal_action": "protect",
        "steps": [
            {
                "observation": (
                    "Wildfire Report — Sector C:\n"
                    "Multiple spot fires and fast wind shifts.\n"
                    "Structures remaining: 20\n"
                    "Wind speed: high\n"
                    "Decision: contain, suppress, or protect."
                ),
                "signals": {
                    "fire_pressure": 0.81,
                    "structure_risk": 0.72,
                    "resource_pressure": 0.62,
                    "ideal_action": "protect",
                },
            }
        ],
    },
}

TASK_NAMES = list(TASKS.keys())

