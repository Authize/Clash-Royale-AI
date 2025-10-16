# 🤖 Automated Clash Royale Bot

## Quick Start

```bash
python launch_bot.py
```

## New Files

- `automated_clash_bot.py` - Main automated bot
- `enhanced_navigation.py` - Smart navigation system  
- `launch_bot.py` - Easy launcher
- `AUTOMATED_BOT_README.md` - This file

## Features

✅ Auto-detects emulators (BlueStacks, LDPlayer, Nox, MEmu)
✅ Continuous AI learning with matches 24/7
✅ Smart navigation with error recovery
✅ Real-time dashboard at http://localhost:8001
✅ Press 'Q' anytime to stop gracefully
✅ Auto-saves models every 5 matches

## Requirements

```bash
pip install torch pyautogui psutil pynput opencv-python numpy pillow python-dotenv inference-sdk
```

## Usage

The bot will:
1. Detect/launch emulator
2. Navigate through all game screens
3. Play matches continuously
4. Learn and improve over time
5. Save progress automatically

Stop anytime by pressing 'Q' key.