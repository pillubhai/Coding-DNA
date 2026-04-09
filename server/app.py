import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

try:
    from models import WildfireAction, WildfireObservation
    from env.wildfire_env import WildfireEnv
    from env.config import Config
    from agents.baseline import BaselineAgent
except (ImportError, ValueError):
    from ..models import WildfireAction, WildfireObservation
    from ..env.wildfire_env import WildfireEnv
    from ..env.config import Config
    from ..agents.baseline import BaselineAgent

import numpy as np

# Score bounds: strictly inside (0, 1) with a safe margin after formatting.
_SCORE_MIN = 0.05
_SCORE_MAX = 0.94

# ── Persistent single env instance ───────────────────────────────────────────
env = WildfireEnv(difficulty="medium")
baseline_agent = BaselineAgent()

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="WildfireContainment-v0",
    description="A dynamic wildfire suppression environment for agentic RL.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/ui", StaticFiles(directory=frontend_dir, html=True), name="frontend")


# ── Core endpoints: /reset, /step (persistent state) ─────────────────────────
@app.post("/reset")
async def reset_env():
    """Reset the environment. Structures stay the same across subsequent /step calls."""
    obs = env.reset()
    return {
        "observation": obs.model_dump(),
        "reward": obs.reward,
        "done": obs.done,
    }


@app.post("/step")
async def step_env(request: Request):
    """Step the SAME environment instance so structures persist across clicks."""
    body = await request.json()
    # Support both {"action": {"actions": [...]}} and {"actions": [...]}
    if "action" in body:
        actions = body["action"].get("actions", [])
    else:
        actions = body.get("actions", [])
    action = WildfireAction(actions=actions)
    obs = env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": obs.reward,
        "done": obs.done,
    }


# ── Info & utility endpoints ─────────────────────────────────────────────────
@app.get("/tasks")
async def get_tasks():
    return {
        "tasks": [
            {"id": "easy", "score": 0.15, "steps": 1000, "ideal_action": "contain", "description": "Low ignition (0.05), 5 structures, slow wind.", "config": {"ignition_prob": Config.EASY["ignition_prob"], "spot_fire_prob": Config.EASY["spot_fire_prob"], "num_structures": Config.EASY["num_structures"]}},
            {"id": "medium", "score": 0.5, "steps": 1000, "ideal_action": "suppress", "description": "Moderate fire (0.12), 10 structures, variable wind.", "config": {"ignition_prob": Config.MEDIUM["ignition_prob"], "spot_fire_prob": Config.MEDIUM["spot_fire_prob"], "num_structures": Config.MEDIUM["num_structures"]}},
            {"id": "hard", "score": 0.9, "steps": 1000, "ideal_action": "protect", "description": "Intense spread (ignition 0.20), frequent spot fires, 20 structures.", "config": {"ignition_prob": Config.HARD["ignition_prob"], "spot_fire_prob": Config.HARD["spot_fire_prob"], "num_structures": Config.HARD["num_structures"]}},
        ],
        "action_schema": WildfireAction.model_json_schema(),
        "observation_schema": WildfireObservation.model_json_schema(),
    }


@app.get("/state")
async def get_state():
    return env.get_state()


@app.get("/schema")
async def get_schema():
    return {
        "action": WildfireAction.model_json_schema(),
        "observation": WildfireObservation.model_json_schema(),
        "state": {
            "type": "object",
            "properties": {
                "episode_id": {"type": "string"},
                "step": {"type": "integer"},
                "difficulty": {"type": "string"},
                "grid_size": {"type": "integer"},
                "max_steps": {"type": "integer"},
                "wind_dir": {"type": "integer"},
                "wind_speed": {"type": "number"},
                "fire_cells": {"type": "integer"},
                "structures_remaining": {"type": "integer"},
                "initial_structures": {"type": "integer"},
                "terminated": {"type": "boolean"},
                "cumulative_reward": {"type": "number"},
            },
        },
    }


@app.get("/metadata")
async def get_metadata():
    return {
        "name": "WildfireContainment-v0",
        "description": "A dynamic wildfire suppression environment for agentic RL.",
    }


@app.post("/mcp")
async def get_mcp():
    return {"jsonrpc": "2.0", "id": None, "result": {"status": "ok"}}


@app.get("/grader")
async def get_grader():
    state = env.get_state()
    initial_structures = state["initial_structures"]
    structures_remaining = state["structures_remaining"]
    fire_cells = state["fire_cells"]
    total_cells = Config.GRID_SIZE * Config.GRID_SIZE
    struct_score = structures_remaining / max(initial_structures, 1)
    fire_score = max(0.0, 1.0 - (fire_cells / total_cells))
    raw_score = (struct_score * 0.6) + (fire_score * 0.4)
    # Hard-clamp: strictly within (0, 1) exclusive
    total_score = round(float(max(_SCORE_MIN, min(_SCORE_MAX, raw_score))), 3)
    return {
        "score": total_score,
        "breakdown": {
            "structure_survival": round(struct_score, 3),
            "fire_suppression": round(fire_score, 3),
            "structures_remaining": structures_remaining,
            "initial_structures": initial_structures,
            "fire_cells": fire_cells,
        }
    }


@app.post("/act")
async def get_agent_action(request: Request):
    """Get the baseline agent's next action for the current observation."""
    obs = env._get_observation(reward=0.0, done=False)
    action = baseline_agent.act(obs)
    # Return raw actions list
    return {
        "actions": [
            {"move": a.move if hasattr(a, 'move') else a.get('move', 8),
             "act": a.act if hasattr(a, 'act') else a.get('act', False)}
            for a in action.actions
        ]
    }


@app.post("/baseline")
async def run_baseline(difficulty: str = Query(default="medium")):
    if difficulty not in ("easy", "medium", "hard"):
        return {"error": "difficulty must be easy, medium, or hard"}
    temp_env = WildfireEnv(difficulty=difficulty)
    obs = temp_env.reset(seed=42)
    initial_structures = int(np.sum(obs.structure_grid))
    total_reward = 0.0
    steps = 0
    while not obs.done and steps < 100:
        action = baseline_agent.act(obs)
        obs = temp_env.step(action)
        total_reward += obs.reward
        steps += 1
    final_structures = int(np.sum(obs.structure_grid))
    fire_cells = int(np.sum(np.array(obs.fire_grid) > 0.1))
    total_cells = Config.GRID_SIZE * Config.GRID_SIZE
    struct_score = final_structures / max(initial_structures, 1)
    fire_score = max(0.0, 1.0 - (fire_cells / total_cells))
    raw_score = (struct_score * 0.6) + (fire_score * 0.4)
    grader_score = round(float(max(_SCORE_MIN, min(_SCORE_MAX, raw_score))), 3)
    return {
        "difficulty": difficulty, "seed": 42, "steps_taken": steps,
        "total_reward": round(total_reward, 3), "done": obs.done,
        "initial_structures": initial_structures, "final_structures": final_structures,
        "fire_cells_remaining": fire_cells, "grader_score": round(grader_score, 3),
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "env": "WildfireContainment-v0", "version": "0.1.0"}


@app.get("/")
async def root():
    index = os.path.join(frontend_dir, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return {"message": "WildfireContainment-v0 is running. See /docs for API."}


def main():
    """Entry point for the server."""
    import uvicorn
    port = int(os.environ.get("PORT", "7860"))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
