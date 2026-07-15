# enjoy.py
import time
from sb3_contrib import MaskablePPO
from caravan_env import CaravanEnv

def watch_multiple_games(num_episodes=10):
    env = CaravanEnv()
    print("Loading trained model weights from caravan_ai_v1.zip...")
    model = MaskablePPO.load("caravan_ai_v1")

    for episode in range(num_episodes):
        obs, info = env.reset()
        done = False
        score = 0
        
        while not done:
            # Retrieve the action mask for the current state
            action_masks = env.get_action_mask(env.player_hand, env.player_board, env.opponent_board)
            
            # Predict the next action using the mask
            action, _states = model.predict(obs, action_masks=action_masks, deterministic=True)
            
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            score += reward
            
            # env.render() # Assuming you have a render method to watch it
            time.sleep(0.5)
            
        print(f"Episode {episode + 1} finished. Total Reward: {score}")

if __name__ == "__main__":
    watch_multiple_games(num_episodes=10)