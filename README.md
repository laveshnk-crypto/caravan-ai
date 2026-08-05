# caravan-ai

`caravan-ai` is a Python project focused on Fallout: New Vegas' Caravan card game. It includes:

- a playable local two-player terminal version of Caravan
- a custom Gymnasium reinforcement learning environment for the game
- a Maskable PPO training script built on `sb3-contrib`
- a small evaluation script for watching a trained agent play games

The current codebase is intentionally small and centered around experimenting with game logic and reinforcement learning rather than packaging or deployment.

## Project structure

- `/home/runner/work/caravan-ai/caravan-ai/main.py` — local terminal game loop for two human players
- `/home/runner/work/caravan-ai/caravan-ai/caravan_game.py` — shared card, hand, deck, and track logic
- `/home/runner/work/caravan-ai/caravan-ai/caravan_env.py` — Gymnasium environment used for training and evaluation
- `/home/runner/work/caravan-ai/caravan-ai/train.py` — Maskable PPO training entry point
- `/home/runner/work/caravan-ai/caravan-ai/enjoy.py` — inference/evaluation script for a saved model
- `/home/runner/work/caravan-ai/caravan-ai/caravan_ai_v1.zip` — saved trained model artifact currently checked into the repository

## What the project does

The repository models a simplified version of Caravan where an agent learns to:

- build caravans toward the scoring window of 21 to 26
- maintain legal ascending or descending caravan sequences
- use face cards tactically on its own or the opponent's caravans
- decide when to discard cards or disband one of its own tracks

The reinforcement learning setup uses action masking so the policy only considers currently legal actions.

## Game model in this repository

This implementation represents the game with three tracks per player and custom rule handling in `/home/runner/work/caravan-ai/caravan-ai/caravan_game.py`.

### Cards

- Number cards and Ace contribute to caravan score
- Ace is valued as `1`
- Jack, Queen, and King are treated as face cards with special behavior

### Track rules implemented here

- Each player owns 3 tracks
- Empty tracks accept any numeric card or Ace
- A track direction is established once two different numeric cards are present
- After direction is established, new numeric cards must continue in that direction unless suit logic allows the play
- Consecutive identical numeric values on the same track are rejected
- Queens can alter track state by changing suit control and flipping direction state during recomputation
- Kings double the value of the previous numeric card when score is calculated
- Jacks remove the targeted top card from a track
- Face cards can only target the current top card of a non-empty track in this implementation

### Win condition implemented here

The game ends when all three tracks are resolved or when a player runs out of cards in hand plus deck.

For each track:

- a caravan is "ready" if its score is between 21 and 26 inclusive
- if only one side is ready, that side wins the track
- if both sides are ready, the higher score wins the track
- equal valid scores leave the track contested

When all tracks are resolved, the player with more track wins wins the round. If both players run out of cards simultaneously or track wins are tied, the result is a draw.

## Reinforcement learning environment

The Gymnasium environment lives in `/home/runner/work/caravan-ai/caravan-ai/caravan_env.py`.

### Action space

The environment uses a flat discrete action space of size `59`.

- `0-7` — discard the card in hand slot `0-7`
- `8-10` — disband one of the player's own tracks
- `11-58` — play a card from one of 8 hand slots onto one of 6 target tracks
  - target tracks `0-2` are the player's own tracks
  - target tracks `3-5` are the opponent's tracks

Only face cards can legally target opponent tracks.

### Observation space

The observation is a 25-element integer vector containing:

- up to 8 hand cards encoded as value/suit pairs
- the 3 player track scores
- the 3 opponent track scores
- the 3 player track directions

### Action masking

The project uses `sb3_contrib` mask support so illegal actions are filtered before policy selection. The mask generation logic is implemented in `CaravanEnv.get_action_mask(...)`.

### Reward shaping

The reward function encourages the agent to:

- move its own caravans into the 21-26 sell window
- keep caravans in that scoring window
- sabotage opponent caravans with face cards
- avoid invalid actions and overshooting above 26

Terminal rewards currently add:

- `+20` for a player win
- `-20` for a player loss

## Requirements

This repository does not currently include a dependency manifest such as `requirements.txt` or `pyproject.toml`, but the source imports show that you need at least:

- Python 3
- `gymnasium`
- `numpy`
- `colorama`
- `sb3-contrib`

Depending on your local setup, `sb3-contrib` may also require the usual Stable Baselines / PyTorch stack.

## Setup

Create and activate a Python virtual environment, then install the required dependencies manually.

Example workflow:

1. Create a virtual environment
2. Activate it
3. Install the required Python packages

Because the repository does not declare pinned dependencies, you may need to choose compatible versions yourself.

## How to run

Run commands from the repository root: `/home/runner/work/caravan-ai/caravan-ai`.

### Play the local terminal game

```bash
python main.py
```

This starts a local two-player terminal session with colored output and interactive prompts.

### Train the RL agent

```bash
python train.py
```

Training uses `MaskablePPO` with:

- `MaskableActorCriticPolicy`
- an `ActionMasker` wrapper
- default learning rate `3e-4`

You can control the number of training timesteps with the `CARAVAN_TRAIN_TIMESTEPS` environment variable:

```bash
CARAVAN_TRAIN_TIMESTEPS=10000 python train.py
```

The trained model is saved as `caravan_ai_v1.zip`.

### Watch a trained model play

```bash
python enjoy.py
```

By default, the script loads `caravan_ai_v1.zip` and runs 10 episodes.

## Notes about the current implementation

- `train.py` includes a small helper that injects `.venv` site-packages into `sys.path` if that directory exists
- `enjoy.py` assumes a trained model file named `caravan_ai_v1.zip` is present in the repository root
- the opponent policy in the Gymnasium environment is a random legal-action player
- there is currently no package layout, CLI, test suite, or formal dependency lockfile in the repository

## Known limitations

- The repository does not currently document or pin dependencies in a package manifest
- There are no automated tests in the repository at present
- The RL opponent is heuristic-free and selects randomly from legal moves
- The environment and local game implement a project-specific ruleset approximation rather than a fully documented official Caravan simulator
- The checked-in model artifact may become stale if training logic changes

## Suggested next improvements

- add a proper `requirements.txt` or `pyproject.toml`
- add automated tests for `CaravanTracks` rules and environment transitions
- document the exact ruleset assumptions against the in-game Caravan rules
- add rendering for evaluation episodes
- separate reusable game logic from scripts into a package structure

## License

See `/home/runner/work/caravan-ai/caravan-ai/LICENSE`.
