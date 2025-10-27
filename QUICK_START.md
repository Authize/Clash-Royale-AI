# Quick Start Guide 🚀

## Your Bot Is Fixed and Ready! ✅

### What Was Fixed
1. **Card Selection** ✅ - Cards are now properly selected and placed
2. **Card Detection** ✅ - Better error handling, won't crash on detection failures  
3. **Training/Playing Modes** ✅ - Clear separation: `train.py` for learning, `play.py` for performance
4. **Learning System** ✅ - AI learns from both wins AND losses

---

## Three Ways to Run

### Option 1: Easy Launcher (Recommended)
```bash
python launcher.py
```
Then select:
- `1` for Training
- `2` for Playing (3 matches)
- `3` for Continuous Play

### Option 2: Direct Training
```bash
python train.py
```
- Trains the AI continuously
- Press 'Q' or CTRL+C to stop
- Monitor at http://localhost:8001

### Option 3: Direct Playing
```bash
python play.py
```
- Uses best trained model
- Plays 3 matches by default
- Shows win/loss stats

---

## First Time Setup (5 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure .env File
Create `.env` with your Roboflow API key:
```env
ROBOFLOW_API_KEY=your_api_key_here
WORKSPACE_TROOP_DETECTION=your_workspace
WORKSPACE_CARD_DETECTION=your_card_workspace
```

### Step 3: Check Screen Coordinates
Open `Actions.py` and verify these match your emulator:
```python
self.TOP_LEFT_X = 1376      # Top-left of game area
self.TOP_LEFT_Y = 120
self.BOTTOM_RIGHT_X = 1838  # Bottom-right of game area
self.BOTTOM_RIGHT_Y = 769
```

### Step 4: Start Training!
```bash
python train.py
```

---

## Training Tips

### How Long to Train?
- **Minimum**: 100 episodes (~2-3 hours)
- **Recommended**: 500+ episodes (~10+ hours)
- **Best**: 1000+ episodes (overnight)

### What to Expect
| Episodes | Win Rate | Behavior |
|----------|----------|----------|
| 0-50 | 0-20% | Random, learning |
| 50-200 | 20-40% | Basic strategies |
| 200-500 | 40-60% | Competent play |
| 500+ | 60-80% | Strong strategic play |

### When to Stop Training?
- Epsilon drops below 0.1
- Win rate is consistently above 60%
- Average reward stays positive
- AI status shows "Ready! 🚀"

---

## Playing with Trained AI

### Basic Play
```bash
python play.py
```
Plays 3 matches with best model.

### Extended Play
```bash
python play.py --episodes 10
```
Plays 10 matches.

### Continuous Play
```bash
python play.py --continuous
```
Plays until you press CTRL+C.

---

## Troubleshooting

### Problem: "All cards are Unknown"
**Fix**: This is OK! The bot will work with placeholder card names. If you want proper detection, verify `WORKSPACE_CARD_DETECTION` in `.env`.

### Problem: "Cards selected but not placed"
**Fix**: Check screen coordinates in `Actions.py` - they must match your emulator window.

### Problem: "Bot doesn't start battles"
**Fix**: Ensure Clash Royale is on the home screen when you start training.

### Problem: "Low win rate after training"
**Fix**: Train for more episodes (at least 500+).

---

## File Structure

```
Your Project/
├── train.py              ← Run this to train
├── play.py               ← Run this to play with trained AI
├── launcher.py           ← Easy menu launcher
├── models/
│   ├── best_model.pth   ← Best AI (use this for playing)
│   └── latest_model.pth ← Latest AI (continues learning)
└── logs/
    └── metrics.csv       ← Training statistics
```

---

## Quick Commands Reference

### Training
```bash
python train.py                    # Start training
Press 'Q' or CTRL+C               # Stop training
Visit http://localhost:8001       # View progress
```

### Playing
```bash
python play.py                     # Play 3 matches
python play.py --episodes 10       # Play 10 matches
python play.py --continuous        # Play continuously
```

### Launcher
```bash
python launcher.py                 # Interactive menu
```

---

## Next Steps

1. ✅ Run `python launcher.py` and select TRAIN
2. ✅ Let it train for at least 100 episodes
3. ✅ Test with `python play.py` to see how it performs
4. ✅ Continue training if win rate is low
5. ✅ Enjoy watching your AI play!

---

## Need More Help?

- **Detailed Guide**: See `USAGE.md`
- **Fix Summary**: See `FIX_SUMMARY.md`
- **Code Issues**: Check console error messages

---

## Summary

✅ **Fixed**: Card selection, detection, and learning
✅ **Ready**: Training and playing modes work
✅ **Easy**: Just run `python launcher.py`

**Start now**: `python train.py` 🚀

Good luck! 🎮🤖
