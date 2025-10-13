Clash Royale RL Agent (Simulator + Emulator Stub)

Overview

This project provides a runnable reinforcement learning setup for a Clash Royale–style environment using a lightweight simulator, a recurrent PPO agent, and an emulator connector stub for deployment. Train the agent in the simulator, then adapt the `EmulatorConnector` to interface with a mobile emulator (only where permitted).

Key components

- Simulator environment: `src/envs/cr_sim_env.py` (Gymnasium-compatible POMDP-style env)
- Recurrent PPO training: `src/train.py` (sb3-contrib RecurrentPPO)
- Custom Dict feature extractor (CNN + MLP): `src/models/feature_extractor.py`
- Emulator integration stub: `src/emulator/connector.py`

Quickstart

1) Create a virtual environment and install dependencies

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

2) Train the agent in the simulator

```bash
python -m src.train --total-steps 200000 --save-dir models/cr_agent
```

3) Evaluate (optional)

```bash
python -m src.train --eval-only --load models/cr_agent/latest.zip
```

4) Emulator connector (stub)

See `src/emulator/connector.py`. It outlines how to:

- Capture a frame (e.g., via ADB screencap) and pre-process to the simulator-like observation format
- Map agent actions (card index + placement) to emulator inputs (e.g., taps/drags)

You must ensure that any integration follows the game and platform terms of service and applicable laws. This repo does not include platform-specific automation bindings.

Notes

- The simulator is intentionally simplified to enable rapid experimentation and to match RL interfaces. It provides spatial observations (grid) and a small context vector (elixir, timers, last-opponent-play features) with a factorized (card, row, col) action.
- The model uses a recurrent policy (LSTM) to handle partial observability and includes hooks for auxiliary tasks (elixir/deck inference) you can extend later.
- For real-time deployment, export the trained model and integrate it with the emulator connector; implement observation extraction and action execution for your emulator.

Commands cheat sheet

```bash
# Train from scratch
python -m src.train --total-steps 1000000 --save-dir models/cr_agent

# Resume training from a checkpoint
python -m src.train --total-steps 200000 --load models/cr_agent/latest.zip --save-dir models/cr_agent

# Short smoke test
python -m src.train --total-steps 20000
```

Disclaimer

Use the emulator connector only where authorized and compliant with terms of service. This project focuses on autonomous learning in a simulator; any external integration is your responsibility.


