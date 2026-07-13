import numpy as np

class CaravanEnv:
    def decode_action(self, action: int):
        # Translates a flat RL integer (0-58) for our action space, into executable Caravan moves
        
        # Check if action is within valid range (0 to 58 inclusive)
        if not (0 <= action <= 58):
            raise ValueError(f"Action {action} is out of bounds for the action space")
        
        # Phase 1: Discard Phase (Actions 0 - 7)
        if 0 <= action <= 7:
            return {'type': 'discard', 'hand_slot': action}
        
        # Phase 2: Disband track Phase (Actions 8 - 10)
        elif 8 <= action <= 10:
            return {'type': 'disband', 'track_index': action - 8} # We do - 8 to map our action space to track indices 0, 1, 2
        
        # Phase 3: Play Phase (Actions 11 - 58)
        else:
            adjusted_play = action - 11 # Adjust the action to start from 0 for the play phase
            hand_slot = adjusted_play // 6 # Determine which hand slot (0-7)
            target_track = adjusted_play % 6 # Determine which track (0-5)

            return {
                "type": "play",
                "hand_slot": hand_slot,
                "target_track": target_track
            }

    def get_action_mask(self, player_hand, player_board, opponent_board) -> np.ndarray:
        # Calculates a binary mask of length 59 for the current turn.
        # True = legal move, False = illegal move

        # Start by assuming all 59 choices are illegal (False)
        mask = np.zeros(59, dtype=bool)

        # Phase 1: Discard masking. (Actions 0 - 7)
        # If hand slot actually holds a card tuple, it is legal to discard
        for hand_slot in range(8):
            if hand_slot < len(player_hand.cards):
                mask[hand_slot] = True
        
        # Phase 2: Disband track masking. (Actions 8 - 10)
        # If the track has at least one card, it is legal to disband
        for track_index in range(3):
            if len(player_board.tracks[track_index]) > 0:
                mask[8 + track_index] = True

        # Phase 3: Play masking. (Actions 11 - 58)
        for hand_slot in range(8):
            # Skip if the hand slot is empty
            if hand_slot >= len(player_hand.cards):
                continue

            card = player_hand.cards[hand_slot]

            for target_track in range(6):
                action_index = 11 + (hand_slot * 6) + target_track

                # Targets 0, 1, 2 are the player's own tracks
                if target_track < 3:
                    if player_board.is_legal_move(target_track, card):
                        mask[action_index] = True
                
                # Targets 3, 4, 5 are the opponent's tracks (Index offset by 3)
                # Only play face cards on OPPONENT tracks and only if the move is legal
                else:
                    opponent_track_index = target_track - 3
                    if card[0] in ['Jack', 'Queen', 'King']:
                        if opponent_board.is_legal_move(opponent_track_index, card):
                            mask[action_index] = True
        return mask
    
    """
    Our list will follow this structure:

    Indices 0-15 (16 numbers) -> Player's hand, 8 cards x 2 suits
    Indices 16-18 (3 numbers) -> Player's tracks scores, 3 tracks x 1 number each
    Indices 19-21 (3 numbers) -> Opponent's tracks scores, 3 tracks x 1 number each
    Indices 22 - 24 (3 numbers) -> Player's tracks directions, 3 tracks x 1 number each
    """

    def encode_state(self, player_hand, player_board, opponent_board) -> np.ndarray:
        # Translates live game objects into a flat vector of 25 integers

        state_vector = []

        # 1. Encode Player Hand (Slots 0 - 15)
        for i in range(8):
            if i < len(player_hand.cards):
                card = player_hand.cards[i] # e.g., ('8', 'Spades')
                card_val = self.VALUE_MAP[card[0]]
                card_suit = self.SUIT_MAP[card[1]]
                state_vector.extend([card_val, card_suit])
            else:
                # If hand has fewer than 8 cards, pad the remaining slots with zeros
                state_vector.extend([0, 0])

        # 2. Encode Player Track Scores (Slots 16 - 18)
        for track_idx in range(3):
            # Calls your engine's score tracker method
            state_vector.append(player_board.get_track_score(track_idx))

        # 3. Encode Opponent Track Scores (Slots 19 - 21)
        for track_idx in range(3):
            state_vector.append(opponent_board.get_track_score(track_idx))

        # 4. Encode Player Track Directions (Slots 22 - 24)
        for track_idx in range(3):
            # Read your engine's track direction string ('Asc', 'Desc', or None)
            raw_dir = player_board.directions[track_idx]
            state_vector.append(self.DIRECTION_MAP.get(raw_dir, 0))

        # Convert to a clean numpy array for neural network compatibility
        return np.array(state_vector, dtype=np.int32)
    
    def step(self, action: int):
        # Executes one environmental turn step based on the agent's action index.
        # Returns (next_observation, reward, terminated, truncated, info)

        # 1. Decode the action number into readable game commands
        move = self.decode_action(action)

        # We will keep tabs on the player's performance to calculate reward
        reward = 0.0

        # 2. Route the decoded move straight to engine instance params
        if move['type'] == 'discard':
            hand_slot = move['hand_slot']

            # remove the card from hand slot and trigger engine's replenish/draw rule
            card_to_discard = self.player_hand.cards.pop(hand_slot)
            self.player_hand.draw(self.deck)  # Assuming your engine has a draw method

            reward += 0.1

        elif move['type'] == 'disband':
            track_index = move['track_index']

            # Remove all cards from the specified track and trigger engine's disband rule
            self.player_board.tracks[track_index] = []
            self.player_board._recompute_track_state(track_index)

            reward += -0.5

        elif move['type'] == 'play':
            hand_slot = move['hand_slot']
            target_track = move['target_track']

            card = self.player_hand.cards.pop(hand_slot)

            # Targets 0, 1, 2 belong to the player's tracks
            if target_track < 3:
                self.player_board.add_to_track(target_track, card)
                
                current_score = self.player_board.get_track_score(target_track)
                if 21 <= current_score <= 26:
                    reward += 2.0
                # Negative feedback
                elif current_score > 26:
                    reward += -2.0
                else:
                    reward += 0.1 # Micro reward for playing a card
            
            # Targets 3, 4, 5 belong to the opponent's tracks
            else:
                opponent_track_index = target_track - 3
                self.opponent_board.add_to_track(opponent_track_index, card)

                # Sabotage rewards! If playing a King on them pushes them over 26 points, do it
                opponent_score = self.opponent_board.get_track_score(opponent_track_index)
                if opponent_score > 26:
                    reward += 3.0 # Massive payoff for sabotage-busting the enemy
                
                # Replenish hand after card play
                self.player_hand.draw(self.deck)

        # 3. Process the opponent's automatic turn phase
        # To train our agent, opponent immediately plays their turn right here.
        # FOr now we will assume a baseline dummy bot plays a legal move

        self.execute_opponent_turn()

        # 4. Compile the final return attributes for the gymnasium compatibility
        next_observation = self.encode_state(self.player_hand, self.player_board, self.opponent_board)
        terminated = self.check_game_over()
        truncated = False

        # If the player won the entire match, shower them in rewards
        if terminated and self.player_won:
            reward += 20.0
        elif terminated and not self.player.won:
            reward += -20.0

        # Action masking dictionary metadata passed into training loop
        info = {
            "action_mask": self.get_action_mask(self.player_hand, self.player_board, self.opponent_board)
        }
        return next_observation, reward, terminated, truncated, info
                



