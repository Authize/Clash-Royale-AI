import os
import glob
import argparse
import time
import json
import torch
from env import ClashRoyaleEnv
from dqn_agent import DQNAgent
from overlay_server import start_overlay_server
from datetime import datetime


def get_latest_model_path(models_dir="models"):
    # First try to use the "latest_model.pth" if it exists
    latest_model = os.path.join(models_dir, "latest_model.pth")
    if os.path.exists(latest_model):
        return latest_model
    
    # Fallback to newest timestamped model
    paths = glob.glob(os.path.join(models_dir, "model_*.pth"))
    if not paths:
        best = os.path.join(models_dir, "best_model.pth")
        return best if os.path.exists(best) else None
    paths.sort()
    return paths[-1]


def main():
    parser = argparse.ArgumentParser(description="Evaluate a saved model (epsilon=0)")
    parser.add_argument("--model", type=str, default=None, help="Path to model .pth file (defaults to best or latest)")
    parser.add_argument("--episodes", type=int, default=3, help="Number of evaluation matches")
    parser.add_argument("--max_steps", type=int, default=2000, help="Max steps per episode")
    parser.add_argument("--no-overlay", action="store_true", help="Disable automatic overlay server")
    args = parser.parse_args()

    # Start overlay server unless disabled
    overlay_server = None
    if not args.no_overlay:
        print("🚀 Starting overlay server...")
        overlay_server = start_overlay_server(port=8001, auto_open=True)
        if not overlay_server:
            print("⚠️  Could not start overlay server, continuing without it...")

    env = ClashRoyaleEnv()
    agent = DQNAgent(env.state_size, env.action_size)

    # Try to use best model first, then latest
    model_path = args.model
    if not model_path:
        # First try best model
        best_model = "models/best_model.pth"
        if os.path.exists(best_model):
            model_path = best_model
            print("🏆 Using BEST model for optimal performance")
        else:
            # Fallback to latest model
            model_path = get_latest_model_path()
            if model_path:
                print("💾 Using LATEST model")
    
    if model_path and os.path.exists(model_path):
        agent.load(os.path.basename(model_path))
        
        # Load model metadata if available
        meta_file = model_path.replace(".pth", "_meta.json").replace("model_", "meta_")
        if not os.path.exists(meta_file):
            meta_file = model_path.replace(".pth", ".json").replace("model_", "meta_")
        if not os.path.exists(meta_file):
            meta_file = "models/best_meta.json" if "best" in model_path else "models/latest_meta.json"
        
        if os.path.exists(meta_file):
            try:
                with open(meta_file, 'r') as f:
                    meta = json.load(f)
                print(f"📊 Model info: Episode {meta.get('episodes', 'Unknown')}, "
                      f"Avg Reward: {meta.get('avg_reward', 'Unknown'):.2f}, "
                      f"Grade: {meta.get('performance_grade', 'Unknown')}")
            except:
                pass
    else:
        print("No saved model found; evaluating with untrained weights.")

    agent.epsilon = 0.0  # greedy policy for evaluation

    # Track rewards for overlay
    all_rewards = []
    
    for ep in range(args.episodes):
        state = env.reset()
        total_reward = 0.0
        steps = 0
        done = False
        print(f"Evaluation match {ep+1} starting...")
        while not done and steps < args.max_steps:
            action = agent.act(state)
            next_state, reward, done = env.step(action)
            state = next_state
            total_reward += reward
            steps += 1
            time.sleep(0.1)  # slow down for visibility
        print(f"Eval {ep+1}: total_reward={total_reward:.2f}, steps={steps}")
        all_rewards.append(total_reward)
        
        # Update overlay data
        if overlay_server:
            avg_reward = sum(all_rewards) / len(all_rewards)
            overlay = {
                "timestamp": datetime.now().isoformat(),
                "episode": ep + 1,
                "epsilon": 0.0,  # Always 0 for evaluation
                "total_reward": float(total_reward),
                "moving_avg_reward": float(avg_reward),
                "rewards_last100": all_rewards[-100:] if len(all_rewards) > 100 else all_rewards,
            }
            try:
                with open("overlay.json", "w") as f:
                    json.dump(overlay, f)
            except Exception as e:
                print(f"Warning: failed to write overlay.json: {e}")

    # Cleanup
    env.close()
    if overlay_server:
        overlay_server.stop_server()
    print("🏁 Evaluation completed!")


if __name__ == "__main__":
    main()

