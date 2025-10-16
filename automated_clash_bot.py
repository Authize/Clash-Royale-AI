
import os
import sys
import time
import psutil
import subprocess
import threading
import signal
from datetime import datetime
from pynput import keyboard

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from env import ClashRoyaleEnv
from dqn_agent import DQNAgent
from Actions import Actions
from overlay_server import start_overlay_server
from enhanced_navigation import EnhancedNavigator

class AutomatedClashBot:
    def __init__(self):
        self.should_stop = False
        self.is_running = False
        self.current_episode = 0
        self.total_matches_played = 0
        self.actions = Actions()
        self.navigator = None
        self.env = None
        self.agent = None
        self.overlay_server = None
        
        self.emulator_process = None
        self.emulator_type = None
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()
        
        print("🤖 Automated Clash Royale AI Bot initialized")
        print("Press 'Q' at any time to stop the bot gracefully")
        
    def on_key_press(self, key):
        try:
            if key.char and key.char.lower() == 'q':
                print("\n🛑 Shutdown requested by user (Q pressed)")
                self.request_stop()
        except AttributeError:
            pass
    
    def request_stop(self):
        self.should_stop = True
        print("🔄 Bot will stop after current match completes...")
        
    def detect_emulators(self):
        print("🔍 Detecting Android emulators...")
        
        # Common emulator process names
        emulator_processes = {
            'bluestacks': ['Bluestacks.exe', 'HD-Player.exe', 'HD-Plus-Service.exe'],
            'ldplayer': ['dnplayer.exe', 'LdVBoxHeadless.exe'],
            'noxplayer': ['Nox.exe', 'NoxVMHandle.exe'],
            'memu': ['MEmu.exe', 'MemuService.exe'],
            'genymotion': ['player.exe', 'genymotion.exe'],
            'android_studio': ['emulator.exe', 'qemu-system-x86_64.exe']
        }
        
        running_emulators = []
        
        for process in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                process_name = process.info['name']
                if process_name:
                    for emulator, processes in emulator_processes.items():
                        if any(proc.lower() in process_name.lower() for proc in processes):
                            running_emulators.append({
                                'type': emulator,
                                'name': process_name,
                                'pid': process.info['pid'],
                                'exe': process.info['exe']
                            })
                            break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if running_emulators:
            print(f"✅ Found {len(running_emulators)} running emulator(s):")
            for emu in running_emulators:
                print(f"  - {emu['type'].title()}: {emu['name']} (PID: {emu['pid']})")
            
            # Use the first detected emulator
            self.emulator_process = running_emulators[0]
            self.emulator_type = running_emulators[0]['type']
            return True
        else:
            print("❌ No Android emulators detected")
            return False
    
    def launch_emulator(self):
        """Launch an Android emulator if none is running"""
        print("🚀 No emulator detected. Attempting to launch one...")
        
        # Common emulator paths
        emulator_paths = {
            'bluestacks': [
                r"C:\Program Files\BlueStacks\HD-Player.exe",
                r"C:\Program Files (x86)\BlueStacks\HD-Player.exe",
                r"C:\ProgramData\BlueStacks\Client\Bluestacks.exe"
            ],
            'ldplayer': [
                r"C:\LDPlayer\LDPlayer4.0\ldplayer.exe",
                r"C:\Program Files\LDPlayer\ldplayer.exe"
            ],
            'noxplayer': [
                r"C:\Program Files\Nox\bin\Nox.exe",
                r"C:\Program Files (x86)\Nox\bin\Nox.exe"
            ],
            'memu': [
                r"C:\Program Files\Microvirt\MEmu\MEmu.exe",
                r"C:\Program Files (x86)\Microvirt\MEmu\MEmu.exe"
            ]
        }
        
        for emulator, paths in emulator_paths.items():
            for path in paths:
                if os.path.exists(path):
                    try:
                        print(f"🚀 Launching {emulator.title()}...")
                        subprocess.Popen([path])
                        time.sleep(10)  # Wait for emulator to start
                        
                        # Check if emulator is now running
                        if self.detect_emulators():
                            print(f"✅ Successfully launched {emulator.title()}")
                            return True
                    except Exception as e:
                        print(f"❌ Failed to launch {emulator}: {e}")
                        continue
        
        print("❌ Could not launch any emulator automatically")
        return False
    
    def wait_for_clash_royale(self):
        """Wait for Clash Royale to be visible/running"""
        print("⏳ Waiting for Clash Royale to be ready...")
        
        # Check for game elements or specific screens
        max_attempts = 30  # 30 attempts = 5 minutes
        attempt = 0
        
        while attempt < max_attempts and not self.should_stop:
            try:
                # Try to detect game UI elements
                if self._detect_game_ready():
                    print("✅ Clash Royale detected and ready!")
                    return True
                
                print(f"🔍 Checking for game... ({attempt + 1}/{max_attempts})")
                time.sleep(10)  # Wait 10 seconds between checks
                attempt += 1
                
            except Exception as e:
                print(f"❌ Error checking for game: {e}")
                time.sleep(5)
                attempt += 1
        
        if attempt >= max_attempts:
            print("⏰ Timeout waiting for Clash Royale. Proceeding anyway...")
            return True
        
        return False
    
    def _detect_game_ready(self):
        """Detect if Clash Royale game is ready"""
        try:
            # Try to detect common game elements
            # This is a simple check - you might need to adjust based on your setup
            
            # Check if we can detect battle button or other UI elements
            if hasattr(self.actions, 'detect_battle_button'):
                if self.actions.detect_battle_button():
                    return True
            
            # Check if we can detect OK button (common across screens)
            if hasattr(self.actions, 'detect_ok_button'):
                if self.actions.detect_ok_button():
                    return True
            
            # Check if we can detect claim button
            if hasattr(self.actions, 'detect_claim_button'):
                if self.actions.detect_claim_button():
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error in game detection: {e}")
            return False
    
    def setup_ai_environment(self):
        """Initialize the AI environment and agent"""
        try:
            print("🧠 Setting up AI environment...")
            
            # Initialize enhanced navigator
            self.navigator = EnhancedNavigator(self.actions)
            print("✅ Enhanced navigator initialized")
            
            # Initialize environment
            self.env = ClashRoyaleEnv()
            print("✅ Game environment initialized")
            
            # Initialize AI agent
            self.agent = DQNAgent(self.env.state_size, self.env.action_size)
            print("✅ AI agent initialized")
            
            # Load existing model if available
            self._load_best_model()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup AI environment: {e}")
            return False
    
    def _load_best_model(self):
        """Load the best available model"""
        try:
            # Try to load best model first
            best_model_path = "models/best_model.pth"
            if os.path.exists(best_model_path):
                self.agent.load("best_model.pth")
                print("🏆 Loaded best model")
                return True
            
            # Try to load latest model
            latest_model_path = "models/latest_model.pth"
            if os.path.exists(latest_model_path):
                self.agent.load("latest_model.pth")
                print("💾 Loaded latest model")
                return True
            
            print("📝 No existing model found - starting from scratch")
            return True
            
        except Exception as e:
            print(f"⚠️ Error loading model: {e}")
            return True  # Continue anyway with untrained model
    
    def start_overlay_server(self):
        """Start the training overlay server"""
        try:
            print("🌐 Starting training overlay server...")
            self.overlay_server = start_overlay_server(port=8001, auto_open=True)
            if self.overlay_server:
                print("✅ Overlay server started at http://localhost:8001")
                return True
            else:
                print("⚠️ Could not start overlay server, continuing without it")
                return False
        except Exception as e:
            print(f"⚠️ Error starting overlay server: {e}")
            return False
    
    def navigate_to_battle(self):
        """Navigate through menus to start a battle using enhanced navigator"""
        try:
            if self.navigator:
                return self.navigator.navigate_to_battle()
            else:
                # Fallback to original navigation
                return self._fallback_navigate_to_battle()
        except Exception as e:
            print(f"❌ Enhanced navigation failed: {e}")
            return self._fallback_navigate_to_battle()
    
    def _fallback_navigate_to_battle(self):
        """Fallback navigation method"""
        try:
            print("🧭 Using fallback navigation to battle...")
            max_attempts = 10
            attempt = 0
            
            while attempt < max_attempts and not self.should_stop:
                try:
                    # Handle various screens that might appear
                    if self._handle_current_screen():
                        print("✅ Successfully navigated to battle")
                        return True
                    
                    attempt += 1
                    time.sleep(2)  # Wait between navigation attempts
                    
                except Exception as e:
                    print(f"❌ Navigation error (attempt {attempt + 1}): {e}")
                    attempt += 1
                    time.sleep(3)
            
            print("⚠️ Could not navigate to battle, but continuing...")
            return True  # Continue anyway
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    def _handle_current_screen(self):
        """Handle the current screen based on what's visible"""
        try:
            # Check for Trophy Road first (highest priority)
            if hasattr(self.actions, 'detect_trophy_road') and self.actions.detect_trophy_road():
                print("🏆 Trophy Road detected - handling...")
                if hasattr(self.actions, 'click_trophy_road_ok'):
                    self.actions.click_trophy_road_ok()
                time.sleep(3)
                return False  # Continue checking screens
            
            # Check for claimable rewards
            if hasattr(self.actions, 'detect_claim_button') and self.actions.detect_claim_button():
                print("🎁 Claim button detected - clicking...")
                if hasattr(self.actions, 'click_claim_button'):
                    self.actions.click_claim_button()
                time.sleep(2)
                return False  # Continue checking screens
            
            # Check for chest screens
            if hasattr(self.actions, 'detect_chest_screen') and self.actions.detect_chest_screen():
                print("📦 Chest screen detected - opening...")
                if hasattr(self.actions, 'open_chest'):
                    self.actions.open_chest()
                time.sleep(3)
                return False  # Continue checking screens
            
            # Check for battle button (main goal)
            if hasattr(self.actions, 'detect_battle_button') and self.actions.detect_battle_button():
                print("⚔️ Battle button detected - starting battle...")
                if hasattr(self.actions, 'click_battle_button'):
                    self.actions.click_battle_button()
                time.sleep(5)  # Wait for battle to start
                return True  # Battle started successfully
            
            # Check for OK buttons (generic handling)
            if hasattr(self.actions, 'detect_ok_button') and self.actions.detect_ok_button():
                print("✅ OK button detected - clicking...")
                if hasattr(self.actions, 'click_ok_button'):
                    self.actions.click_ok_button()
                time.sleep(2)
                return False  # Continue checking screens
            
            # If no specific screen detected, try smart button click
            print("🤔 No specific screen detected, trying smart navigation...")
            if hasattr(self.actions, 'smart_button_click'):
                self.actions.smart_button_click()
                time.sleep(3)
            
            return False  # Continue checking
            
        except Exception as e:
            print(f"Error handling current screen: {e}")
            return False
    
    def play_match(self):
        """Play a single match with AI learning"""
        try:
            print(f"\n🎮 Starting match #{self.total_matches_played + 1}")
            
            # Reset environment for new match
            state = self.env.reset()
            total_reward = 0.0
            steps = 0
            max_steps = 2000
            done = False
            
            print("🤖 AI is now playing...")
            
            # Play the match
            while not done and steps < max_steps and not self.should_stop:
                try:
                    # AI decides action
                    action = self.agent.act(state)
                    
                    # Execute action in environment
                    next_state, reward, done = self.env.step(action)
                    
                    # Agent learns from experience
                    self.agent.remember(state, action, reward, next_state, done)
                    
                    # Train the agent
                    if len(self.agent.memory) > 32:
                        self.agent.replay(32)
                    
                    # Update state and tracking
                    state = next_state
                    total_reward += reward
                    steps += 1
                    
                    # Small delay to prevent overwhelming the system
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"❌ Error during match step {steps}: {e}")
                    time.sleep(1)
                    continue
            
            # Match completed
            self.total_matches_played += 1
            self.current_episode += 1
            
            # Determine outcome
            if done:
                if total_reward > 50:
                    outcome = "victory"
                    print(f"🏆 VICTORY! Match #{self.total_matches_played} - Reward: {total_reward:.2f}")
                elif total_reward < -50:
                    outcome = "defeat"
                    print(f"💔 DEFEAT! Match #{self.total_matches_played} - Reward: {total_reward:.2f}")
                else:
                    outcome = "draw"
                    print(f"🤝 DRAW! Match #{self.total_matches_played} - Reward: {total_reward:.2f}")
            else:
                outcome = "timeout"
                print(f"⏰ TIMEOUT! Match #{self.total_matches_played} - Reward: {total_reward:.2f}")
            
            # Update agent with match outcome
            if hasattr(self.agent, 'update_game_outcome'):
                game_data = {
                    "episode": self.current_episode,
                    "total_reward": total_reward,
                    "steps": steps,
                    "outcome": outcome,
                    "duration": steps * 0.1
                }
                self.agent.update_game_outcome(outcome, total_reward, game_data)
            
            # Save model periodically
            self._save_model_if_needed()
            
            return outcome
            
        except Exception as e:
            print(f"❌ Error during match: {e}")
            return "error"
    
    def _save_model_if_needed(self):
        """Save model periodically"""
        try:
            # Save every 5 matches
            if self.total_matches_played % 5 == 0:
                # Ensure models directory exists
                os.makedirs("models", exist_ok=True)
                
                # Save current model
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                model_path = f"models/model_{timestamp}.pth"
                
                import torch
                torch.save(self.agent.model.state_dict(), model_path)
                
                # Also save as latest
                latest_path = "models/latest_model.pth"
                torch.save(self.agent.model.state_dict(), latest_path)
                
                print(f"💾 Model saved after {self.total_matches_played} matches")
                
        except Exception as e:
            print(f"⚠️ Error saving model: {e}")
    
    def run(self):
        """Main bot loop"""
        try:
            print("🚀 Starting Automated Clash Royale AI Bot...")
            self.is_running = True
            
            # Step 1: Detect or launch emulator
            if not self.detect_emulators():
                if not self.launch_emulator():
                    print("❌ Cannot proceed without an emulator. Please start one manually.")
                    return False
            
            # Step 2: Wait for Clash Royale to be ready
            if not self.wait_for_clash_royale():
                print("❌ Game not ready, but proceeding anyway...")
            
            # Step 3: Setup AI environment
            if not self.setup_ai_environment():
                print("❌ Failed to setup AI environment")
                return False
            
            # Step 4: Start overlay server
            self.start_overlay_server()
            
            print("🎯 Bot is ready! Starting continuous play...")
            print("📊 Training data will be visible at http://localhost:8001")
            print("⏹️  Press 'Q' at any time to stop gracefully")
            
            # Main game loop
            consecutive_errors = 0
            max_consecutive_errors = 5
            
            while not self.should_stop:
                try:
                    # Navigate to battle
                    if not self.navigate_to_battle():
                        print("⚠️ Navigation issues, but continuing...")
                    
                    # Play a match
                    outcome = self.play_match()
                    
                    # Reset error counter on successful match
                    if outcome != "error":
                        consecutive_errors = 0
                    else:
                        consecutive_errors += 1
                    
                    # Check for too many consecutive errors
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"❌ Too many consecutive errors ({consecutive_errors}). Taking a longer break...")
                        time.sleep(30)  # Long break
                        consecutive_errors = 0
                    
                    # Short break between matches
                    if not self.should_stop:
                        print("😴 Brief pause before next match...")
                        time.sleep(5)
                    
                except KeyboardInterrupt:
                    print("\n🛑 Keyboard interrupt received")
                    self.request_stop()
                    break
                except Exception as e:
                    print(f"❌ Unexpected error in main loop: {e}")
                    consecutive_errors += 1
                    time.sleep(10)
            
            print("🏁 Bot stopped gracefully")
            return True
            
        except Exception as e:
            print(f"❌ Critical error in bot: {e}")
            return False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            print("🧹 Cleaning up...")
            
            self.is_running = False
            
            # Save final model
            if self.agent and self.total_matches_played > 0:
                try:
                    import torch
                    os.makedirs("models", exist_ok=True)
                    final_path = "models/final_model.pth"
                    torch.save(self.agent.model.state_dict(), final_path)
                    print(f"💾 Final model saved: {final_path}")
                except Exception as e:
                    print(f"⚠️ Error saving final model: {e}")
            
            # Close environment
            if self.env:
                try:
                    self.env.close()
                    print("✅ Environment closed")
                except Exception as e:
                    print(f"⚠️ Error closing environment: {e}")
            
            # Stop overlay server
            if self.overlay_server:
                try:
                    self.overlay_server.stop_server()
                    print("✅ Overlay server stopped")
                except Exception as e:
                    print(f"⚠️ Error stopping overlay server: {e}")
            
            # Stop keyboard listener
            if hasattr(self, 'keyboard_listener'):
                try:
                    self.keyboard_listener.stop()
                    print("✅ Keyboard listener stopped")
                except Exception as e:
                    print(f"⚠️ Error stopping keyboard listener: {e}")
            
            print(f"📊 Final Stats:")
            print(f"  - Total matches played: {self.total_matches_played}")
            print(f"  - Episodes completed: {self.current_episode}")
            
            # Print navigation stats if available
            if self.navigator:
                try:
                    nav_stats = self.navigator.get_navigation_stats()
                    print(f"  - Navigation stats: {nav_stats['screen_states']}")
                    print(f"  - Recovery attempts: {nav_stats['recovery_attempts']}")
                except Exception as e:
                    print(f"  - Navigation stats unavailable: {e}")
            
            print("🎯 Bot cleanup completed")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    print(f"\n🛑 Received signal {signum}")
    # The bot will handle cleanup in its main loop
    pass

def main():
    """Main entry point"""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("🤖 AUTOMATED CLASH ROYALE AI BOT")
    print("=" * 60)
    print("This bot will:")
    print("  1. Detect/launch Android emulator")
    print("  2. Wait for Clash Royale to be ready")
    print("  3. Navigate menus automatically")
    print("  4. Play matches continuously with AI learning")
    print("  5. Save progress and models automatically")
    print("=" * 60)
    print("⏹️  Press 'Q' at any time to stop gracefully")
    print("📊 Training dashboard: http://localhost:8001")
    print("=" * 60)
    
    # Create and run bot
    bot = AutomatedClashBot()
    
    try:
        success = bot.run()
        if success:
            print("✅ Bot completed successfully")
        else:
            print("❌ Bot encountered errors")
    except KeyboardInterrupt:
        print("\n🛑 Bot interrupted by user")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
        import traceback
        traceback.print_exc()
    
    print("👋 Goodbye!")

if __name__ == "__main__":
    main()