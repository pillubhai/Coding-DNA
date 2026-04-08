"""
Greedy heuristic baseline agent for WildfireContainment-v0.
Deterministic, no learning. Must fail in hard mode by design.
"""
import numpy as np
try:
    from models import WildfireAction, WildfireObservation
    from env.config import Config
except (ImportError, ValueError):
    from ..models import WildfireAction, WildfireObservation
    from ..env.config import Config


class UnitAction:
    """Simple action container (mirrors Pydantic model for internal use)."""
    def __init__(self, move: int = 8, act: bool = False):
        self.move = move
        self.act = act


# Direction vectors: N, NE, E, SE, S, SW, W, NW
DIRS = [(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1)]


def _best_move_toward(current_pos, target_pos):
    """Return direction index (0-7) that moves closest to target, or 8 to stay."""
    if current_pos == target_pos:
        return 8
    r, c = current_pos
    tr, tc = target_pos
    dr = tr - r
    dc = tc - c
    best_dir = 8
    best_score = -1
    for i, (ddr, ddc) in enumerate(DIRS):
        score = ddr * dr + ddc * dc
        if score > best_score:
            best_score = score
            best_dir = i
    return best_dir


def _find_nearest_fire_near_structure(fire_grid, structure_grid, pos):
    """
    Find the nearest burning cell that is adjacent to a structure.
    Falls back to nearest burning cell if none found near a structure.
    """
    fire_arr = np.array(fire_grid)
    struct_arr = np.array(structure_grid)
    size = fire_arr.shape[0]
    r, c = pos

    # Collect burning cells
    burning = np.argwhere(fire_arr > 0.1)
    if len(burning) == 0:
        return None

    # Prefer cells near structures
    priority = []
    fallback = []
    for br, bc in burning:
        # Check if any neighbour is a structure
        near_struct = False
        for dr, dc in DIRS:
            nr, nc = br + dr, bc + dc
            if 0 <= nr < size and 0 <= nc < size and struct_arr[nr, nc] == 1:
                near_struct = True
                break
        dist = abs(br - r) + abs(bc - c)
        if near_struct:
            priority.append((dist, [int(br), int(bc)]))
        else:
            fallback.append((dist, [int(br), int(bc)]))

    if priority:
        priority.sort()
        return priority[0][1]
    if fallback:
        fallback.sort()
        return fallback[0][1]
    return None


def _find_nearest_burning(fire_grid, pos):
    """Find nearest burning cell to pos."""
    fire_arr = np.array(fire_grid)
    burning = np.argwhere(fire_arr > 0.1)
    if len(burning) == 0:
        return None
    r, c = pos
    dists = [abs(br - r) + abs(bc - c) for br, bc in burning]
    idx = int(np.argmin(dists))
    return [int(burning[idx][0]), int(burning[idx][1])]


def _needs_refill(unit):
    if unit["type"] == "tanker":
        return unit["resource"] < 2.0
    return unit["resource"] < 10.0


def _at_base(unit):
    """Edge = refill zone."""
    r, c = unit["pos"]
    return r == 0 or c == 0


class BaselineAgent:
    """
    Greedy heuristic agent:
    - Tanker: flies toward fire near structures, drops water, refills at edge.
    - Crew1 & Crew2: move toward nearest fire, suppress.
    Works reasonably on easy/medium. Fails on hard (by design per PRD).
    """

    def act(self, obs: WildfireObservation) -> WildfireAction:
        fire_grid = obs.fire_grid
        structure_grid = obs.structure_grid
        units = obs.units

        actions = []

        for i, unit in enumerate(units):
            unit_dict = {
                "type": unit.type,
                "pos": list(unit.pos),
                "resource": unit.resource,
            }

            if _needs_refill(unit_dict) and not _at_base(unit_dict):
                # Move toward top-left corner (base)
                move = _best_move_toward(unit_dict["pos"], [0, 0])
                actions.append(UnitAction(move=move, act=False))
                continue

            if unit.type == "tanker":
                target = _find_nearest_fire_near_structure(
                    fire_grid, structure_grid, unit_dict["pos"]
                )
                if target is None:
                    actions.append(UnitAction(move=8, act=False))
                    continue
                if unit_dict["pos"] == target:
                    # Drop water
                    actions.append(UnitAction(move=8, act=True))
                else:
                    move = _best_move_toward(unit_dict["pos"], target)
                    # Drop while adjacent to fire
                    dist = abs(unit_dict["pos"][0] - target[0]) + abs(unit_dict["pos"][1] - target[1])
                    act = dist <= 1 and unit.resource >= 2.0
                    actions.append(UnitAction(move=move, act=act))

            else:  # ground_crew
                target = _find_nearest_burning(fire_grid, unit_dict["pos"])
                if target is None:
                    actions.append(UnitAction(move=8, act=False))
                    continue
                if unit_dict["pos"] == target:
                    actions.append(UnitAction(move=8, act=True))
                else:
                    move = _best_move_toward(unit_dict["pos"], target)
                    actions.append(UnitAction(move=move, act=False))

        # Build WildfireAction-compatible list
        # Convert back to Pydantic-compatible dicts
        try:
            from models import WildfireAction as WA
        except ImportError:
            from ..models import WildfireAction as WA

        # Build raw action list that WildfireAction expects
        raw_actions = [{"move": a.move, "act": a.act} for a in actions]
        return WA(actions=raw_actions)
