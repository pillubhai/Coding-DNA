# tasks/graders.py
# Reward functions for wildfire tasks. All rewards are kept strictly inside (0, 1).

def grade_action(task_id: str, action: str, signals: dict) -> float:
    """
    Score one action for a wildfire task.
    Always returns a value in (0, 1).
    """
    action = (action or "").lower().strip()
    if action not in ("contain", "suppress", "protect"):
        for candidate in ("contain", "suppress", "protect"):
            if candidate in action:
                action = candidate
                break
        else:
            return 0.1

    raw_score = 0.5
    if task_id == "easy":
        raw_score = _grade_easy(action, signals)
    elif task_id == "medium":
        raw_score = _grade_medium(action, signals)
    elif task_id == "hard":
        raw_score = _grade_hard(action, signals)
    elif task_id == "extreme":
        raw_score = _grade_extreme(action, signals)

    return round(min(max(raw_score, 0.05), 0.94), 3)


def _grade_easy(action: str, signals: dict) -> float:
    fire_pressure = signals.get("fire_pressure", 0.5)
    structure_risk = signals.get("structure_risk", 0.5)
    if action == "contain":
        return round(0.62 + 0.2 * (1.0 - fire_pressure) + 0.1 * (1.0 - structure_risk), 3)
    if action == "suppress":
        return round(0.4 + 0.1 * (1.0 - fire_pressure), 3)
    return 0.12


def _grade_medium(action: str, signals: dict) -> float:
    fire_pressure = signals.get("fire_pressure", 0.5)
    structure_risk = signals.get("structure_risk", 0.5)
    if action == "suppress":
        return round(0.65 + 0.18 * fire_pressure + 0.07 * structure_risk, 3)
    if action == "protect":
        return round(0.45 + 0.12 * structure_risk, 3)
    return 0.15


def _grade_hard(action: str, signals: dict) -> float:
    fire_pressure = signals.get("fire_pressure", 0.5)
    structure_risk = signals.get("structure_risk", 0.5)
    if action == "protect":
        return round(0.7 + 0.15 * structure_risk, 3)
    if action == "suppress":
        return round(0.5 + 0.1 * fire_pressure, 3)
    return 0.12


def _grade_extreme(action: str, signals: dict) -> float:
    fire_pressure = signals.get("fire_pressure", 0.5)
    structure_risk = signals.get("structure_risk", 0.5)
    if action == "protect":
        return round(0.72 + 0.12 * fire_pressure + 0.08 * structure_risk, 3)
    if action == "suppress":
        return round(0.48 + 0.1 * fire_pressure, 3)
    return 0.14
