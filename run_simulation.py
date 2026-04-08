import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from env.wildfire_env import WildfireEnv
from agents.baseline import BaselineAgent
from render.renderer import WildfireRenderer

def run_simulation(steps=50):
    print(f"Starting Wildfire Simulation ({steps} steps)...")
    env = WildfireEnv(difficulty="medium")
    obs = env.reset(seed=42)
    agent = BaselineAgent()
    
    for i in range(steps):
        action = agent.act(obs)
        obs = env.step(action)
        
        if (i + 1) % 10 == 0:
            fire_count = np.sum(np.array(obs.fire_grid) > 0.1)
            struct_count = np.sum(obs.structure_grid)
            print(f"Step {i+1:3}: Fire Cells={fire_count:3}, Structures={struct_count:2}, Total Reward={obs.reward:6.2f}")
            
        if obs.done:
            print(f"Simulation ended at step {i+1} (Reason: {'Contained' if np.sum(obs.fire_grid) <= 0 else 'Lost/Max Steps'})")
            break
            
    # Render final state
    print("Rendering final state...")
    fig = WildfireRenderer.render(obs, title=f"Final State (Step {i+1})")
    
    # Save to artifacts directory (assuming we are in the brain folder context for artifacts)
    # Actually, as per instructions, I should save to the current directory and then maybe the user can see it.
    # Or I'll save it to the Desktop/OpenEnv folder.
    save_path = "wildfire_final_state.png"
    plt.savefig(save_path)
    print(f"Saved visualization to {save_path}")
    plt.close(fig)

if __name__ == "__main__":
    run_simulation()
