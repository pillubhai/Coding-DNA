import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from env.wildfire_env import WildfireEnv
from agents.baseline import BaselineAgent
import numpy as np

def verify():
    print("Initializing WildfireEnv (medium)...")
    env = WildfireEnv(difficulty="medium")
    
    print("Resetting environment...")
    obs = env.reset(seed=42)
    
    print(f"Initial reward: {obs.reward}")
    print(f"Num units: {len(obs.units)}")
    print(f"Structure count: {np.sum(obs.structure_grid)}")
    
    agent = BaselineAgent()
    
    print("Taking 5 steps with BaselineAgent...")
    for i in range(5):
        action = agent.act(obs)
        obs = env.step(action)
        print(f"Step {i+1}: Reward={obs.reward:.4f}, Done={obs.done}, Fire Intensity Sum={np.sum(obs.fire_grid):.2f}")
        
    print("\nVerification Successful!")

if __name__ == "__main__":
    try:
        verify()
    except Exception as e:
        print(f"Verification Failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
