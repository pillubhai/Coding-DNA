# tasks/definitions.py
# Synthetic wildfire tasks for grading and validation.

TASKS = {
    "easy": {
        "description": "Low ignition wildfire with few structures and slow wind.",
        "ideal_action": "contain",
        "steps": [
            {
                "observation": (
                    "Wildfire Report - Sector A1:\n"
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
            },
            {
                "observation": (
                    "Wildfire Report - Sector A2:\n"
                    "Spot fires are appearing near the northern edge.\n"
                    "Structures remaining: 5\n"
                    "Wind speed: low\n"
                    "Decision: contain, suppress, or protect."
                ),
                "signals": {
                    "fire_pressure": 0.27,
                    "structure_risk": 0.20,
                    "resource_pressure": 0.14,
                    "ideal_action": "contain",
                },
            },
            {
                "observation": (
                    "Wildfire Report - Sector A3:\n"
                    "Fire is slowing after a small containment line.\n"
                    "Structures remaining: 5\n"
                    "Wind speed: low\n"
                    "Decision: contain, suppress, or protect."
                ),
                "signals": {
                    "fire_pressure": 0.19,
                    "structure_risk": 0.15,
                    "resource_pressure": 0.10,
                    "ideal_action": "contain",
                },
            },
        ],
    },
    "medium": {
        "description": "Moderate wildfire spread with variable wind and limited time.",
        "ideal_action": "suppress",
        "steps": [
            {
                "observation": (
                    "Wildfire Report - Sector B1:\n"
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
            },
            {
                "observation": (
                    "Wildfire Report - Sector B2:\n"
                    "Wind shifts are pushing the line eastward.\n"
                    "Structures remaining: 10\n"
                    "Wind speed: medium\n"
                    "Decision: contain, suppress, or protect."
                ),
                "signals": {
                    "fire_pressure": 0.60,
                    "structure_risk": 0.52,
                    "resource_pressure": 0.37,
                    "ideal_action": "suppress",
                },
            },
            {
                "observation": (
                    "Wildfire Report - Sector B3:\n"
                    "Suppression crews are holding the line but fire is still active.\n"
                    "Structures remaining: 10\n"
                    "Wind speed: medium\n"
                    "Decision: contain, suppress, or protect."
                ),
                "signals": {
                    "fire_pressure": 0.53,
                    "structure_risk": 0.44,
                    "resource_pressure": 0.30,
                    "ideal_action": "suppress",
                },
            },
        ],
    },
    "hard": {
        "description": "Intense wildfire spread with frequent spot fires and high structure exposure.",
        "ideal_action": "protect",
        "steps": [
            {
                "observation": (
                    "Wildfire Report - Sector C1:\n"
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
            },
            {
                "observation": (
                    "Wildfire Report - Sector C2:\n"
                    "Spot fires are jumping the containment line.\n"
                    "Structures remaining: 20\n"
                    "Wind speed: high\n"
                    "Decision: contain, suppress, or protect."
                ),
                "signals": {
                    "fire_pressure": 0.84,
                    "structure_risk": 0.76,
                    "resource_pressure": 0.66,
                    "ideal_action": "protect",
                },
            },
            {
                "observation": (
                    "Wildfire Report - Sector C3:\n"
                    "Several homes remain exposed on the downwind flank.\n"
                    "Structures remaining: 20\n"
                    "Wind speed: high\n"
                    "Decision: contain, suppress, or protect."
                ),
                "signals": {
                    "fire_pressure": 0.79,
                    "structure_risk": 0.70,
                    "resource_pressure": 0.60,
                    "ideal_action": "protect",
                },
            },
        ],
    },
    "extreme": {
        "description": "Extreme wildfire spread with overwhelming fire pressure and scarce resources.",
        "ideal_action": "protect",
        "steps": [
            {
                "observation": (
                    "Wildfire Report - Sector D1:\n"
                    "Multiple fronts are advancing rapidly.\n"
                    "Structures remaining: 25\n"
                    "Wind speed: extreme\n"
                    "Decision: contain, suppress, or protect."
                ),
                "signals": {
                    "fire_pressure": 0.92,
                    "structure_risk": 0.86,
                    "resource_pressure": 0.78,
                    "ideal_action": "protect",
                },
            },
            {
                "observation": (
                    "Wildfire Report - Sector D2:\n"
                    "Fire lines are overloaded and crews are running low on water.\n"
                    "Structures remaining: 25\n"
                    "Wind speed: extreme\n"
                    "Decision: contain, suppress, or protect."
                ),
                "signals": {
                    "fire_pressure": 0.94,
                    "structure_risk": 0.89,
                    "resource_pressure": 0.82,
                    "ideal_action": "protect",
                },
            },
            {
                "observation": (
                    "Wildfire Report - Sector D3:\n"
                    "A critical structure cluster remains under direct threat.\n"
                    "Structures remaining: 25\n"
                    "Wind speed: extreme\n"
                    "Decision: contain, suppress, or protect."
                ),
                "signals": {
                    "fire_pressure": 0.90,
                    "structure_risk": 0.84,
                    "resource_pressure": 0.76,
                    "ideal_action": "protect",
                },
            },
        ],
    },
}

TASK_NAMES = list(TASKS.keys())
