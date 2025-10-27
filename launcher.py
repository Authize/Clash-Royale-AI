#!/usr/bin/env python3
"""
Clash Royale AI Bot Launcher
Quick access to train and play modes
"""

import sys
import subprocess
import os

def print_banner():
    print("=" * 60)
    print("🤖 CLASH ROYALE AI BOT")
    print("=" * 60)
    print()

def print_menu():
    print("Select mode:")
    print()
    print("  1. 🏆 TRAIN - Train the AI to play (continuous learning)")
    print("  2. 🎮 PLAY  - Use trained AI to play (3 matches)")
    print("  3. ♾️  PLAY  - Continuous play mode")
    print("  4. 🤖 AUTO  - Automated bot (auto-start battles)")
    print("  5. ❓ HELP  - Show usage guide")
    print("  6. ❌ EXIT  - Quit")
    print()

def show_help():
    print("\n📖 HELP - Usage Information\n")
    print("TRAIN MODE:")
    print("  - Trains the AI from scratch or continues from latest model")
    print("  - Learns from both wins and losses")
    print("  - Saves best models automatically")
    print("  - Press 'Q' to stop training\n")
    
    print("PLAY MODE:")
    print("  - Uses the best trained model")
    print("  - No exploration (epsilon=0)")
    print("  - Shows win/loss statistics\n")
    
    print("AUTO MODE:")
    print("  - Fully automated gameplay")
    print("  - Handles menus and navigation")
    print("  - Starts battles automatically\n")
    
    print("For detailed information, see USAGE.md\n")
    input("Press ENTER to continue...")

def run_train():
    print("\n🏆 Starting Training Mode...\n")
    try:
        subprocess.run([sys.executable, "train.py"], cwd=os.path.dirname(__file__))
    except KeyboardInterrupt:
        print("\n⏸️  Training stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def run_play(continuous=False):
    mode = "Continuous" if continuous else "3 matches"
    print(f"\n🎮 Starting Play Mode ({mode})...\n")
    try:
        cmd = [sys.executable, "play.py"]
        if continuous:
            cmd.append("--continuous")
        subprocess.run(cmd, cwd=os.path.dirname(__file__))
    except KeyboardInterrupt:
        print("\n⏸️  Play stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def run_auto():
    print("\n🤖 Starting Automated Bot...\n")
    try:
        subprocess.run([sys.executable, "automated_clash_bot.py"], cwd=os.path.dirname(__file__))
    except KeyboardInterrupt:
        print("\n⏸️  Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def main():
    while True:
        print_banner()
        print_menu()
        
        try:
            choice = input("Enter choice (1-6): ").strip()
            
            if choice == "1":
                run_train()
            elif choice == "2":
                run_play(continuous=False)
            elif choice == "3":
                run_play(continuous=True)
            elif choice == "4":
                run_auto()
            elif choice == "5":
                show_help()
            elif choice == "6":
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please enter 1-6.\n")
                input("Press ENTER to continue...")
            
            print()  # Add spacing
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            input("Press ENTER to continue...")

if __name__ == "__main__":
    main()
