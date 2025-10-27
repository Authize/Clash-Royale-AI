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
    print("=" * 60)
    print("🎮 CLASH ROYALE AI - PLAY MODE")
    print("=" * 60)
    print("This will use the trained AI to play Clash Royale.")
    print("")
    
    parser = argparse.ArgumentParser(
        description="Play Clash Royale with trained AI (no exploration)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python play.py                    # Play 3 matches with best model
  python play.py --episodes 10      # Play 10 matches
  python play.py --model models/latest_model.pth  # Use specific model
        """
    )
    parser.add_argument("--model", type=str, default=None, 
                        help="Path to model .pth file (defaults to best or latest)")
    parser.add_argument("--episodes", type=int, default=3, 
                        help="Number of matches to play (default: 3)")
    parser.add_argument("--max_steps", type=int, default=2000, 
                        help="Max steps per match (default: 2000)")
    parser.add_argument("--no-overlay", action="store_true", 
                        help="Disable training overlay dashboard")
    parser.add_argument("--continuous", action="store_true",
                        help="Play continuously until interrupted")
    args = parser.parse_args()
    
    print(f"⚙️  Configuration:")
    print(f"  - Matches: {args.episodes if not args.continuous else 'Continuous'}")
    print(f"  - Model: {args.model if args.model else 'Best available'}")
    print(f"  - Overlay: {'Disabled' if args.no_overlay else 'Enabled'}")
    print("=" * 60)
    print("")

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

    # Set epsilon to 0 for pure exploitation (no exploration)
    agent.epsilon = 0.0
    print("🎯 AI set to pure exploitation mode (epsilon=0.0)")
    print("")

    # Track rewards for overlay
    all_rewards = []
    wins = 0
    losses = 0
    draws = 0
    
    # Determine number of episodes
    episodes = float('inf') if args.continuous else args.episodes
    ep = 0
    
    try:
        while ep < episodes:
            ep += 1
            print(f"🎮 Match {ep}/{args.episodes if not args.continuous else '∞'} starting...")
            
            state = env.reset()
            total_reward = 0.0
            steps = 0
            done = False
            
            while not done and steps < args.max_steps:
                action = agent.act(state)
                next_state, reward, done = env.step(action)
                state = next_state
                total_reward += reward
                steps += 1
                time.sleep(0.1)  # slow down for visibility
            
            # Determine outcome
            if total_reward > 50:
                outcome = "victory"
                wins += 1
                print(f"✅ Match {ep}: VICTORY! Reward: {total_reward:.2f}, Steps: {steps}")
            elif total_reward < -50:
                outcome = "defeat"
                losses += 1
                print(f"❌ Match {ep}: DEFEAT! Reward: {total_reward:.2f}, Steps: {steps}")
            else:
                outcome = "draw"
                draws += 1
                print(f"🤝 Match {ep}: DRAW! Reward: {total_reward:.2f}, Steps: {steps}")
            
            all_rewards.append(total_reward)
            
            # Print current statistics
            print(f"📊 Current Stats: W:{wins} L:{losses} D:{draws} | Avg Reward: {sum(all_rewards)/len(all_rewards):.2f}")
            print("")
            
            # Update overlay data
            if overlay_server:
                avg_reward = sum(all_rewards) / len(all_rewards)
                win_rate = (wins / len(all_rewards)) * 100 if len(all_rewards) > 0 else 0
                overlay = {
                    "timestamp": datetime.now().isoformat(),
                    "episode": ep,
                    "epsilon": 0.0,  # Always 0 for play mode
                    "total_reward": float(total_reward),
                    "moving_avg_reward": float(avg_reward),
                    "rewards_last100": all_rewards[-100:] if len(all_rewards) > 100 else all_rewards,
                    "mode": "PLAY",
                    "wins": wins,
                    "losses": losses,
                    "draws": draws,
                    "win_rate": win_rate,
                }
                try:
                    with open("overlay.json", "w") as f:
                        json.dump(overlay, f)
                except Exception as e:
                    print(f"Warning: failed to write overlay.json: {e}")
                    
    except KeyboardInterrupt:
        print("\n⏸️  Play interrupted by user")
    
    # Print final statistics
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULTS")
    print("=" * 60)
    print(f"Total Matches: {len(all_rewards)}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Draws: {draws}")
    if len(all_rewards) > 0:
        win_rate = (wins / len(all_rewards)) * 100
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Average Reward: {sum(all_rewards)/len(all_rewards):.2f}")
    print("=" * 60)

    # Cleanup
    env.close()
    if overlay_server:
        overlay_server.stop_server()
    print("🏁 Evaluation completed!")


if __name__ == "__main__":
    main()

