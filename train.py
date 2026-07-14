import os
import sys
from pathlib import Path


def _bootstrap_venv_site_packages():
    repo_root = Path(__file__).resolve().parent
    venv_site_packages = repo_root / ".venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"

    if venv_site_packages.exists():
        site_packages_path = str(venv_site_packages)
        if site_packages_path not in sys.path:
            sys.path.insert(0, site_packages_path)


_bootstrap_venv_site_packages()

from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy

from caravan_env import CaravanEnv

# Define how stable-baselines3 retrieves the mask from your environment
def mask_fn(env: CaravanEnv):
    return env.get_action_mask(env.player_hand, env.player_board, env.opponent_board)

# Initialize the Caravan environment
env = CaravanEnv()

# Wrap it in the ActionMasker
env = ActionMasker(env, mask_fn)

# Instantiate the Maskable PPO network
model = MaskablePPO(MaskableActorCriticPolicy, env, verbose=1, learning_rate=3e-4)

# Start training the model!
print("Beginning AI training loop...")
total_timesteps = int(os.environ.get("CARAVAN_TRAIN_TIMESTEPS", "1000000"))
model.learn(total_timesteps=total_timesteps)

# Save the brain!
model.save("caravan_ai_v1")
print("Model saved successfully as caravan_ai_v1.zip!")