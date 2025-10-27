# Clash Royale AI Bot - Usage Guide

## Overview
This AI bot learns to play Clash Royale using Deep Q-Learning (DQN). It has two modes: **Training** and **Playing**.

## Recent Fixes ✅
- **Fixed Card Selection**: The bot now properly selects and places cards using keyboard shortcuts (1-4)
- **Improved Card Detection**: Better error handling and fallback for card detection failures
- **Separate Training/Play Modes**: Clear separation between learning and playing with the best model
- **Enhanced Learning**: The AI learns from both wins AND losses, adapting strategies

## Prerequisites

1. **Android Emulator** (BlueStacks, LDPlayer, NoxPlayer, or similar)
2. **Clash Royale** installed and running in the emulator
3. **Python 3.8+** installed
4. **Roboflow API Key** configured in `.env` file

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file with:
```env
ROBOFLOW_API_KEY=your_api_key_here
WORKSPACE_TROOP_DETECTION=your_workspace_name
WORKSPACE_CARD_DETECTION=your_card_workspace_name
INFERENCE_API_URL=http://localhost:9001
```

### 3. Adjust Screen Coordinates
The bot is configured for Windows. If you have a different setup, edit `Actions.py`:
```python
# In Actions.py, update these coordinates for your emulator window:
self.TOP_LEFT_X = 1376      # Top-left X of game area
self.TOP_LEFT_Y = 120       # Top-left Y of game area
self.BOTTOM_RIGHT_X = 1838  # Bottom-right X of game area
self.BOTTOM_RIGHT_Y = 769   # Bottom-right Y of game area

# Card bar coordinates (where your 4 cards appear):
self.CARD_BAR_X = 1450
self.CARD_BAR_Y = 847
```

## Usage

### Training Mode 🏆
Train the AI to learn from matches:

```bash
python train.py
```

**What it does:**
- Starts from scratch or continues from latest model
- Plays matches continuously
- Learns from both victories and defeats
- Saves the best model automatically
- Shows real-time progress at http://localhost:8001
- Press 'Q' or CTRL+C to stop

**Training Tips:**
- Let it train for at least 100+ episodes
- The AI gets better over time as epsilon (exploration) decreases
- Best models are saved in `models/best_model.pth`
- Training data is logged to `logs/metrics.csv`

### Play Mode 🎮
Use the trained AI to play at its best:

```bash
# Play 3 matches with the best model
python play.py

# Play 10 matches
python play.py --episodes 10

# Play continuously until interrupted
python play.py --continuous

# Use a specific model
python play.py --model models/latest_model.pth

# Disable overlay dashboard
python play.py --no-overlay
```

**What it does:**
- Loads the best available model
- Sets epsilon to 0 (pure exploitation, no exploration)
- Plays optimally based on training
- Tracks wins, losses, and draws
- Shows performance statistics

## Understanding the AI

### Card Selection System
The bot uses keyboard shortcuts to select cards:
- Press `1` → Select first card
- Press `2` → Select second card  
- Press `3` → Select third card
- Press `4` → Select fourth card

Then clicks on the screen to place the card.

### Card Detection
The bot uses Roboflow API to detect which cards are in hand:
- Captures screenshots of the card bar
- Splits into 4 individual card images
- Sends to Roboflow for identification
- Falls back to generic "Card_1", "Card_2", etc. if detection fails

### Learning System
The AI learns through:
1. **Rewards for good actions**: Reducing enemy presence, destroying towers
2. **Penalties for mistakes**: Wasting elixir, letting enemies through
3. **Loss Analysis**: When the AI loses, it analyzes what went wrong and adapts
4. **Win Streaks**: Tracks and celebrates winning streaks
5. **Strategy Adaptation**: Adjusts tactics based on recent performance

## Common Issues & Fixes

### Issue: "All cards are Unknown"
**Cause**: Card detection API not working or cards not visible
**Fix**:
- Ensure `WORKSPACE_CARD_DETECTION` is set in `.env`
- Check if Roboflow API is accessible
- The bot will still work with placeholder card names

### Issue: "Cards selected but not placed"
**Cause**: Screen coordinates might be wrong
**Fix**:
- Take a screenshot during battle
- Measure the game area coordinates
- Update coordinates in `Actions.py`

### Issue: "Bot clicks battle button repeatedly"
**Cause**: Battle button detection issues
**Fix**:
- Check if button images exist in `images/buttons/` folder
- Try lowering confidence threshold in `detect_battle_button()`

### Issue: "Bot not learning well"
**Cause**: Needs more training time
**Fix**:
- Train for at least 100-500 episodes
- Check reward signals in the logs
- Monitor epsilon decay (should decrease over time)

## File Structure

```
Clash-Royale-AI/
├── train.py                 # Training script
├── play.py                  # Playing script
├── automated_clash_bot.py   # Automated bot runner
├── env.py                   # Game environment
├── dqn_agent.py            # Deep Q-Learning agent
├── Actions.py              # Screen interaction and card placement
├── models/                 # Saved models
│   ├── best_model.pth     # Best performing model
│   ├── latest_model.pth   # Most recent model
│   └── model_*.pth        # Timestamped models
├── logs/                   # Training logs
│   └── metrics.csv        # Performance metrics
├── screenshots/            # Captured screenshots
└── overlay.json           # Real-time training data
```

## Model Files

- **best_model.pth**: Model with highest average reward (use this for playing)
- **latest_model.pth**: Most recent model (continues learning)
- **model_YYYYMMDD_HHMMSS.pth**: Timestamped checkpoints

## Advanced Configuration

### Adjust Learning Rate
In `dqn_agent.py`:
```python
self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)  # Default
```

### Adjust Exploration
In `dqn_agent.py`:
```python
self.epsilon = 1.0          # Initial exploration (100%)
self.epsilon_min = 0.01     # Minimum exploration (1%)
self.epsilon_decay = 0.997  # Decay rate per episode
```

### Adjust Rewards
In `env.py` `_compute_reward()` method:
- Modify reward values for different actions
- Add new reward signals
- Adjust penalties

## Monitoring Training

### Real-time Dashboard
Visit http://localhost:8001 while training to see:
- Current episode and reward
- Moving average performance
- Win streak information
- Training progress
- AI readiness status

### CSV Logs
Check `logs/metrics.csv` for:
- Episode-by-episode performance
- Epsilon values over time
- Total rewards
- Average rewards

## Tips for Better Performance

1. **Start with Training**: Always train before playing
2. **Let it Learn from Losses**: The AI adapts after defeats
3. **Monitor Epsilon**: When epsilon is low (<0.1), the AI is mostly exploiting learned strategies
4. **Save Checkpoints**: Models are auto-saved every 5 matches
5. **Use Best Model**: For best performance, always use `best_model.pth`

## Troubleshooting

### Bot runs but doesn't do anything
- Check if the game window coordinates are correct
- Ensure the emulator is in focus
- Verify keyboard shortcuts work (1-4 keys)

### Training crashes
- Check Roboflow API connection
- Ensure enough disk space for models
- Verify `.env` file is configured correctly

### Low win rate
- Train for more episodes (500+)
- Check reward signals are appropriate
- Monitor if the bot is placing cards effectively

## Next Steps

After following this guide:
1. ✅ Fix any coordinate/detection issues
2. ✅ Train the AI for 100+ episodes
3. ✅ Test with `play.py` to see performance
4. ✅ Continue training if needed
5. ✅ Experiment with reward tuning

## Support

For issues:
1. Check the console output for error messages
2. Verify all prerequisites are installed
3. Ensure emulator and game are running
4. Check coordinates match your setup

Good luck training your Clash Royale AI! 🎮🤖
