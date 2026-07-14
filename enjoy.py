# enjoy.py
import time
from sb3_contrib import MaskablePPO
from caravan_env import CaravanEnv

def watch_multiple_games(num_episodes=1):
    env = CaravanEnv()
    print("Loading trained model weights from caravan_ai_v1.zip...")
    model = MaskablePPO.load("caravan_ai_v1")
    
    ai_wins = 0
    bot_wins = 0
    draws = 0

    for episode in range(1, num_episodes + 1):
        obs, info = env.reset()
        terminated = False
        truncated = False
        turn_count = 0
        
        print(f"\n==========================================")
        print(f"🎮 STARTING EVALUATION MATCH {episode}/{num_episodes}")
        print(f"==========================================")
        time.sleep(1.0)
        
        while not (terminated or truncated):
            turn_count += 1
            action_mask = env.get_action_mask(env.player_hand, env.player_board, env.opponent_board)
            action, _states = model.predict(obs, action_masks=action_mask, deterministic=True)
            
            decoded_move = env.decode_action(int(action))
            obs, reward, terminated, truncated, info = env.step(int(action))
            
            # Print status periodically or on game end to prevent terminal flooding
            if terminated or truncated or turn_count % 15 == 0:
                print(f"\n⚡ Match {episode} - Turn {turn_count}")
                print(f"🤖 AI Last Move: {decoded_move}")
                print("--- Current Track Scores ---")
                for i in range(3):
                    p1_score = env.player_board.get_track_score(i)
                    p2_score = env.opponent_board.get_track_score(i)
                    print(f"Track {i}: AI Score [{p1_score:02d}] vs Opponent Score [{p2_score:02d}]")
        
        # Track Standings
        if env.player_won:
            ai_wins += 1
            print(f"\n🎉 MATCH {episode} RESULT: True AI Victory!")
        elif env.opponent_won:
            bot_wins += 1
            print(f"\n💀 MATCH {episode} RESULT: Opponent Bot Wins.")
        else:
            draws += 1
            print(f"\n🤝 MATCH {episode} RESULT: Deadlock Draw.")
            
        time.sleep(2.0)

    print("\n==========================================")
    print("🏆 FINAL EVALUATION STANDINGS 🏆")
    print(f"==========================================")
    print(f"🥇 Trained AI Agent Wins: {ai_wins}")
    print(f"🥈 Random House Bot Wins: {bot_wins}")
    print(f"🤝 Match Deadlock Draws:  {draws}")
    print("==========================================")

if __name__ == "__main__":
    watch_multiple_games(num_episodes=5)