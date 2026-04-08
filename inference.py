"""
inference.py — LLM Baseline Agent for WildfireContainment-v0
Root-level inference script. Required by OpenEnv Hackathon spec.

Usage:
    export API_BASE_URL=https://api-inference.huggingface.co/v1
    export MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
    export HF_TOKEN=hf_your_token_here
    python inference.py

Logs follow the mandatory [START] / [STEP] / [END] format.
"""

import os
import sys
import json
import time

# ── Required env vars ────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api-inference.huggingface.co/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME",   "meta-llama/Llama-3.1-8B-Instruct")
HF_TOKEN     = os.environ.get("HF_TOKEN",     "")

if not HF_TOKEN:
    print("[WARN] HF_TOKEN not set — using greedy fallback agent (no LLM calls)")

# ── Imports ──────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARN] openai package not installed — using greedy fallback")

from env.wildfire_env import WildfireEnv
from env.config import Config
from agents.baseline import BaselineAgent
import numpy as np

# ── OpenAI client (uses HF_TOKEN + API_BASE_URL) ─────────────────────────────
client = None
if OPENAI_AVAILABLE and HF_TOKEN:
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

# ── Greedy fallback agent ────────────────────────────────────────────────────
greedy_agent = BaselineAgent()

# ── System prompt for LLM agent ──────────────────────────────────────────────
SYSTEM_PROMPT = """You are controlling a wildfire suppression team on a 20x20 grid.
You control 3 units: 1 Air Tanker and 2 Ground Crews.
Each step you must choose actions for all 3 units.

Actions per unit:
- move: 0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW, 8=Stay
- act: true to drop water (Tanker) or suppress fire (Crew), false otherwise

Respond ONLY with a valid JSON object in this exact format:
{"actions": [{"move": <int>, "act": <bool>}, {"move": <int>, "act": <bool>}, {"move": <int>, "act": <bool>}]}

Priority: protect structures (value=5x penalty), suppress intense fire near structures.
Units at corners [0,0], [19,0], [0,19] will automatically refill resources.
"""


def build_prompt(obs) -> str:
    fire_arr = np.array(obs.fire_grid)
    burning_cells = int(np.sum(fire_arr > 0.1))
    structures = int(np.sum(obs.structure_grid))
    units_info = "\n".join([
        f"  Unit {i} ({u.type}): pos={list(u.pos)}, resource={u.resource:.1f}"
        for i, u in enumerate(obs.units)
    ])
    return (
        f"Step info:\n"
        f"  Burning cells: {burning_cells}\n"
        f"  Structures remaining: {structures}\n"
        f"  Wind direction: {obs.wind_dir}, speed: {obs.wind_speed:.2f}\n"
        f"Units:\n{units_info}\n\n"
        f"Choose actions for [Tanker, Crew1, Crew2]:"
    )


def llm_action(obs):
    """Try LLM action, fall back to greedy on any failure."""
    if client is None:
        return greedy_agent.act(obs)
    try:
        prompt = build_prompt(obs)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.0,
            max_tokens=120,
            timeout=15,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        from models import WildfireAction
        return WildfireAction(actions=data["actions"])
    except Exception:
        return greedy_agent.act(obs)


def compute_grader_score(obs, initial_structures: int) -> float:
    fire_arr = np.array(obs.fire_grid)
    fire_cells = int(np.sum(fire_arr > 0.1))
    total_cells = Config.GRID_SIZE * Config.GRID_SIZE
    structures_remaining = int(np.sum(obs.structure_grid))
    struct_score = structures_remaining / max(initial_structures, 1)
    fire_score   = max(0.0, 1.0 - (fire_cells / total_cells))
    return round(float(np.clip((struct_score * 0.6) + (fire_score * 0.4), 0.0, 1.0)), 4)


def run_episode(difficulty: str, task_id: str, seed: int = 42):
    """Run one full episode and emit mandatory log format."""
    env = WildfireEnv(difficulty=difficulty)
    obs = env.reset(seed=seed)

    initial_structures = int(np.sum(obs.structure_grid))
    cumulative_reward  = 0.0

    # ── [START] log ──────────────────────────────────────────────────────────
    start_data = json.dumps({
        "task_id":            task_id,
        "difficulty":         difficulty,
        "seed":               seed,
        "initial_structures": initial_structures,
        "grid_size":          Config.GRID_SIZE,
        "max_steps":          Config.MAX_STEPS,
        "model":              MODEL_NAME,
    })
    print(f"[START] {start_data}", flush=True)

    step = 0
    while not obs.done and step < Config.MAX_STEPS:
        action = llm_action(obs)
        obs    = env.step(action)
        cumulative_reward += obs.reward
        step  += 1

        fire_cells          = int(np.sum(np.array(obs.fire_grid) > 0.1))
        structures_now      = int(np.sum(obs.structure_grid))
        grader_score        = compute_grader_score(obs, initial_structures)

        # ── [STEP] log ───────────────────────────────────────────────────────
        step_data = json.dumps({
            "task_id":            task_id,
            "step":               step,
            "reward":             round(float(obs.reward), 4),
            "cumulative_reward":  round(float(cumulative_reward), 4),
            "done":               obs.done,
            "fire_cells":         fire_cells,
            "structures":         structures_now,
            "grader_score":       grader_score,
        })
        print(f"[STEP] {step_data}", flush=True)

    final_score = compute_grader_score(obs, initial_structures)

    # ── [END] log ────────────────────────────────────────────────────────────
    end_data = json.dumps({
        "task_id":            task_id,
        "difficulty":         difficulty,
        "total_steps":        step,
        "cumulative_reward":  round(float(cumulative_reward), 4),
        "final_grader_score": final_score,
        "structures_saved":   int(np.sum(obs.structure_grid)),
        "initial_structures": initial_structures,
        "fire_contained":     bool(np.sum(np.array(obs.fire_grid) > 0.1) == 0),
        "model":              MODEL_NAME,
    })
    print(f"[END] {end_data}", flush=True)

    return final_score


def main():
    tasks = [
        ("easy",   "easy"),
        ("medium", "medium"),
        ("hard",   "hard"),
    ]

    all_scores = {}
    for difficulty, task_id in tasks:
        score = run_episode(difficulty=difficulty, task_id=task_id, seed=42)
        all_scores[task_id] = score

    # Final summary
    avg = round(sum(all_scores.values()) / len(all_scores), 4)
    summary_data = json.dumps({
        "scores":  all_scores,
        "average": avg,
    })
    print(f"[SUMMARY] {summary_data}", flush=True)


if __name__ == "__main__":
    main()
