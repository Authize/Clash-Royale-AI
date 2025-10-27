import os
import torch
import glob
import json
import random
import numpy as np
from collections import deque
from env import ClashRoyaleEnv
from dqn_agent import DQNAgent
from pynput import keyboard
from professional_training_monitor import professional_monitor
from enhanced_learning_system import EnhancedLearningSystem
from datetime import datetime
from overlay_server import start_overlay_server

class KeyboardController:
    def __init__(self):
        self.should_exit = False
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def on_press(self, key):
        try:
            if key.char == 'q':
                print("\nShutdown requested - cleaning up...")
                self.should_exit = True
        except AttributeError:
            pass  # Special key pressed
            
    def is_exit_requested(self):
        return self.should_exit

def get_latest_model_path(models_dir="models"):
    model_files = glob.glob(os.path.join(models_dir, "model_*.pth"))
    if not model_files:
        return None
    model_files.sort()  # Lexicographical sort works for timestamps
    return model_files[-1]

def train():
    # Start overlay server
    print("🚀 Starting overlay server...")
    overlay_server = start_overlay_server(port=8001, auto_open=True)
    if not overlay_server:
        print("⚠️  Could not start overlay server, continuing without it...")
    
    env = ClashRoyaleEnv()
    agent = DQNAgent(env.state_size, env.action_size)
    
    # Initialize enhanced learning system
    enhanced_learning = EnhancedLearningSystem()

    # Ensure models directory exists
    os.makedirs("models", exist_ok=True)

    # Load latest model if available
    latest_model = get_latest_model_path("models")
    if latest_model:
        agent.load(os.path.basename(latest_model))
        # Load epsilon
        meta_path = latest_model.replace("model_", "meta_").replace(".pth", ".json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
                agent.epsilon = meta.get("epsilon", 1.0)
            print(f"Epsilon loaded: {agent.epsilon}")

    controller = KeyboardController()
    episodes = 10000
    batch_size = 32
    max_steps_per_episode = 2000

    # Track moving average reward and best model
    recent_rewards = deque(maxlen=50)
    best_avg_reward = float('-inf')
    # Tracking for dashboard overlay and CSV logging
    os.makedirs("logs", exist_ok=True)
    overlay_history = deque(maxlen=100)

    for ep in range(episodes):
        if controller.is_exit_requested():
            print("Training interrupted by user.")
            break

        state = env.reset()
        print(f"Episode {ep + 1} starting. Epsilon: {agent.epsilon:.3f}")
        total_reward = 0
        done = False
        steps = 0
        while not done and steps < max_steps_per_episode:
            action = agent.act(state)
            next_state, reward, done = env.step(action)
            agent.remember(state, action, reward, next_state, done)
            agent.replay(batch_size)
            
            # Update professional data collection
            if hasattr(agent, 'update_professional_data'):
                agent.update_professional_data(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            steps += 1
        
        # Determine game outcome and update win streak
        game_outcome = "unknown"
        if done:
            if total_reward > 50:  # Victory threshold
                game_outcome = "victory"
            elif total_reward < -50:  # Defeat threshold
                game_outcome = "defeat"
            else:
                game_outcome = "draw"
        
        # Update win streak and learn from losses
        if game_outcome != "unknown":
            game_data = {
                "episode": ep + 1,
                "total_reward": total_reward,
                "steps": steps,
                "outcome": game_outcome,
                "duration": steps * 0.1,  # Estimate duration
                "elixir_waste": "high" if total_reward < -30 else "low",
                "failed_strategies": ["aggressive"] if total_reward < -50 else [],
                "enemy_successful_patterns": ["swarm"] if total_reward < -40 else [],
                "successful_strategies": ["defensive"] if total_reward > 30 else [],
                "damage_dealt": max(0, total_reward * 2),
                "damage_taken": max(0, -total_reward * 2),
                "tower_damage": max(0, total_reward * 1.5),
                "enemy_tower_damage": max(0, total_reward * 1.2),
                "battle_phase": "mid",  # Could be determined from game state
                "enemy_deck_type": "unknown",
                "difficulty_level": "medium"
            }
            agent.update_game_outcome(game_outcome, total_reward, game_data)
            
            # Enhanced learning analysis
            game_analysis = enhanced_learning.analyze_game(game_data)
            if game_analysis:
                print(f"🧠 Enhanced learning analysis: {game_analysis.outcome}")
                
                # Get learning recommendations
                recommendations = enhanced_learning.get_learning_recommendations()
                if recommendations:
                    print(f"💡 Learning recommendations: {len(recommendations)}")
                    for rec in recommendations[:3]:  # Show top 3
                        print(f"   - {rec['title']}: {rec['action']}")
            
            # Adapt strategies based on recent losses
            agent.adapt_strategy_based_on_losses()
        
        print(f"Episode {ep + 1}: Total Reward = {total_reward:.2f}, Epsilon = {agent.epsilon:.3f}")
        
        # Display win streak info
        streak_info = agent.get_win_streak_info()
        print(f"🏆 Win Streak: {streak_info['current_streak']} | Best: {streak_info['best_streak']} | Win Rate: {streak_info['win_rate']:.1f}%")
        
        # Update professional training monitor
        professional_monitor.update_training_data(ep + 1, total_reward, steps, agent)

        # Update moving average and save best model
        recent_rewards.append(total_reward)
        avg_reward = sum(recent_rewards) / len(recent_rewards)
        print(f"Moving Avg(50) Reward = {avg_reward:.2f}")

        # Track best model with more comprehensive metrics
        if len(recent_rewards) >= 10 and avg_reward > best_avg_reward:
            best_avg_reward = avg_reward
            best_path = os.path.join("models", "best_model.pth")
            torch.save(agent.model.state_dict(), best_path)
            
            # Save comprehensive best model metadata
            best_meta = {
                "epsilon": float(agent.epsilon),
                "avg_reward": float(best_avg_reward),
                "episodes": ep + 1,
                "total_reward": float(total_reward),
                "timestamp": datetime.now().isoformat(),
                "training_hours": (ep + 1) * 0.1,  # Estimate
                "performance_grade": "A" if avg_reward > 80 else "B" if avg_reward > 60 else "C" if avg_reward > 40 else "D"
            }
            
            with open(os.path.join("models", "best_meta.json"), "w") as f:
                json.dump(best_meta, f)
            print(f"🏆 NEW BEST MODEL! Episode {ep + 1}: avg={best_avg_reward:.2f}, grade={best_meta['performance_grade']}")
            
            # Also update the best model to be the latest for continued learning
            latest_best_path = os.path.join("models", "latest_best_model.pth")
            torch.save(agent.model.state_dict(), latest_best_path)
            print(f"💾 Best model also saved as latest_best_model.pth for continued learning")

        # Append to overlay history and write overlay.json for dashboard
        overlay_history.append(float(total_reward))
        
        # Calculate training progress
        training_progress = min(100, max(0, (ep + 1) / 10))  # 0-100% based on episodes
        if agent.epsilon < 0.1:
            training_progress += 20  # Bonus for low epsilon
        if avg_reward > 50:
            training_progress += 15  # Bonus for good rewards
        training_progress = min(100, training_progress)
        
        # Determine AI readiness
        if ep < 100:
            ai_status = "Learning..."
        elif ep < 500:
            ai_status = "Training..."
        elif ep < 1000:
            if avg_reward > 30:
                ai_status = "Getting Good!"
            else:
                ai_status = "Improving..."
        else:
            if avg_reward > 50 and agent.epsilon < 0.2:
                ai_status = "Ready! 🚀"
            elif avg_reward > 20:
                ai_status = "Good! 👍"
            else:
                ai_status = "Still Learning..."
        
        # Get win streak information
        streak_info = agent.get_win_streak_info()
        
        # Get enhanced learning summary
        learning_summary = enhanced_learning.get_learning_summary()
        
        overlay = {
            "timestamp": datetime.now().isoformat(),
            "episode": ep + 1,
            "epsilon": float(agent.epsilon),
            "total_reward": float(total_reward),
            "moving_avg_reward": float(avg_reward),
            "rewards_last100": list(overlay_history),
            "training_progress": float(training_progress),
            "ai_status": ai_status,
            "win_streak": streak_info['current_streak'],
            "best_streak": streak_info['best_streak'],
            "win_rate": streak_info['win_rate'],
            "total_wins": streak_info['total_wins'],
            "total_losses": streak_info['total_losses'],
            "game_outcome": game_outcome,
            "learning_insights": learning_summary.get('learning_insights', 0),
            "recent_performance": learning_summary.get('recent_performance', {}),
            "recommendations_count": len(learning_summary.get('recommendations', []))
        }
        try:
            with open("overlay.json", "w") as f:
                json.dump(overlay, f)
        except Exception as e:
            print(f"Warning: failed to write overlay.json: {e}")

        # Append to CSV log
        try:
            csv_line = f"{datetime.now().isoformat()},{ep+1},{total_reward:.4f},{avg_reward:.4f},{agent.epsilon:.6f}\n"
            with open(os.path.join("logs", "metrics.csv"), "a", newline="") as f:
                f.write(csv_line)
        except Exception as e:
            print(f"Warning: failed to write logs/metrics.csv: {e}")

        # Save model after every episode for continuous learning
        agent.update_target_model()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join("models", f"model_{timestamp}.pth")
        torch.save(agent.model.state_dict(), model_path)
        with open(os.path.join("models", f"meta_{timestamp}.json"), "w") as f:
            json.dump({"epsilon": float(agent.epsilon), "episode": ep + 1, "total_reward": float(total_reward), "avg_reward": float(avg_reward)}, f)
        print(f"💾 Model saved after episode {ep + 1}: {model_path}")
        
        # Also save a "latest" model for easy access
        latest_model_path = os.path.join("models", "latest_model.pth")
        torch.save(agent.model.state_dict(), latest_model_path)
        with open(os.path.join("models", "latest_meta.json"), "w") as f:
            json.dump({"epsilon": float(agent.epsilon), "episode": ep + 1, "total_reward": float(total_reward), "avg_reward": float(avg_reward)}, f)
        print(f"💾 Latest model updated: {latest_model_path}")

    # Cleanup
    env.close()
    if overlay_server:
        overlay_server.stop_server()
    print("🏁 Training completed!")

if __name__ == "__main__":
    print("=" * 60)
    print("🏆 CLASH ROYALE AI - TRAINING MODE")
    print("=" * 60)
    print("This will train the AI to play Clash Royale.")
    print("")
    print("⚠️  Make sure:")
    print("  1. Clash Royale is running in an emulator")
    print("  2. You're on the home screen or ready to battle")
    print("  3. Roboflow API keys are configured in .env")
    print("")
    print("📊 Training will:")
    print("  - Learn from both wins and losses")
    print("  - Save best models automatically")
    print("  - Display progress at http://localhost:8001")
    print("  - Run continuously until you press 'Q'")
    print("")
    print("⏸️  Press CTRL+C or 'Q' to stop training gracefully")
    print("=" * 60)
    print("")
    
    input("▶️  Press ENTER to start training...")
    
    # Set seeds for reproducibility where possible
    try:
        seed = int(os.getenv("SEED", "42"))
    except Exception:
        seed = 42
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    print("✅ Starting training...\n")
    train()
