import random
import gymnasium as gym
from gymnasium import spaces
import numpy as np

from caravan_game import CaravanDeck, CaravanTracks, PlayerHand


class CaravanEnv(gym.Env):
    VALUE_MAP = {
        "Ace": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "10": 10,
        "Jack": 11,
        "Queen": 12,
        "King": 13,
    }

    SUIT_MAP = {
        "Hearts": 1,
        "Diamonds": 2,
        "Clubs": 3,
        "Spades": 4,
    }

    DIRECTION_MAP = {
        None: 0,
        "Asc": 1,
        "Desc": -1,
    }

    def __init__(self):
        super(CaravanEnv, self).__init__()
        
        # 1. Define the Action Space (59 flat discrete buttons)
        self.action_space = spaces.Discrete(59)
        
        # 2. Define the Observation Space (25 flat numeric state attributes)
        self.observation_space = spaces.Box(
            low=-1, high=100, shape=(25,), dtype=np.int32
        )
        
        # 3. Structural placeholders (These get populated cleanly inside self.reset())
        self.player_deck = None
        self.opponent_deck = None
        self.deck = None
        self.player_hand = None
        self.opponent_hand = None
        self.player_board = None
        self.opponent_board = None
        
        self.player_won = False
        self.opponent_won = False
        self.terminated = False

    def reset(self, seed=None, options=None):
        if seed is not None:
            import random
            random.seed(seed)
            np.random.seed(seed)

        self.player_deck = CaravanDeck()
        self.opponent_deck = CaravanDeck()
        self.deck = self.player_deck

        self.player_hand = PlayerHand()
        self.player_hand.draw_initial_hand(self.player_deck)

        self.opponent_hand = PlayerHand()
        self.opponent_hand.draw_initial_hand(self.opponent_deck)

        self.player_board = CaravanTracks()
        self.opponent_board = CaravanTracks()

        self.player_won = False
        self.opponent_won = False
        self.terminated = False

        # --- "First Wave" Initial Seeding (Self-Contained Fix) ---
        # Draw 1 numerical starter card (Ace through 10) directly onto each track
        for track_idx in range(3):
            
            # Player Track Seeding
            while True:
                # Safely pop a card from your engine's card list
                card = self.player_deck.cards.pop(0) 
                if card[0] not in ['Jack', 'Queen', 'King']:
                    self.player_board.tracks[track_idx].append(card)
                    self.player_board.directions[track_idx] = 'Unassigned'
                    break
                else:
                    # Put face cards back at the bottom of the deck if drawn early
                    self.player_deck.cards.append(card)

            # Opponent Track Seeding
            while True:
                opp_card = self.opponent_deck.cards.pop(0)
                if opp_card[0] not in ['Jack', 'Queen', 'King']:
                    self.opponent_board.tracks[track_idx].append(opp_card)
                    self.opponent_board.directions[track_idx] = 'Unassigned'
                    break
                else:
                    self.opponent_deck.cards.append(opp_card)

        # Encode state and mask based on the actual starting wave board
        observation = self.encode_state(self.player_hand, self.player_board, self.opponent_board)
        info = {
            "action_mask": self.get_action_mask(self.player_hand, self.player_board, self.opponent_board)
        }
        return observation, info

    def decode_action(self, action: int):
        # Translates a flat RL integer (0-58) into executable Caravan moves.
        if not 0 <= action <= 58:
            raise ValueError(f"Action {action} is out of bounds for the action space")

        if 0 <= action <= 7:
            return {"type": "discard", "hand_slot": action}

        if 8 <= action <= 10:
            return {"type": "disband", "track_index": action - 8}

        adjusted_play = action - 11
        hand_slot = adjusted_play // 6
        target_track = adjusted_play % 6
        return {
            "type": "play",
            "hand_slot": hand_slot,
            "target_track": target_track,
        }

    def _face_card_can_target_top(self, board, track_index: int) -> bool:
        return 0 <= track_index < 3 and len(board.tracks[track_index]) > 0

    def get_action_mask(self, player_hand, player_board, opponent_board) -> np.ndarray:
        mask = np.zeros(59, dtype=bool)

        for hand_slot in range(8):
            if hand_slot < len(player_hand.cards):
                mask[hand_slot] = True

        for track_index in range(3):
            if len(player_board.tracks[track_index]) > 0:
                mask[8 + track_index] = True

        for hand_slot in range(8):
            if hand_slot >= len(player_hand.cards):
                continue

            card = player_hand.cards[hand_slot]
            is_face_card = card[0] in ["Jack", "Queen", "King"]

            for target_track in range(6):
                action_index = 11 + (hand_slot * 6) + target_track

                if target_track < 3:
                    if is_face_card:
                        if self._face_card_can_target_top(player_board, target_track):
                            mask[action_index] = True
                    elif player_board.is_legal_move(target_track, card):
                        mask[action_index] = True
                else:
                    opponent_track_index = target_track - 3
                    if is_face_card and self._face_card_can_target_top(opponent_board, opponent_track_index):
                        mask[action_index] = True

        return mask

    def encode_state(self, player_hand, player_board, opponent_board) -> np.ndarray:
        state_vector = []

        for i in range(8):
            if i < len(player_hand.cards):
                card = player_hand.cards[i]
                card_val = self.VALUE_MAP[card[0]]
                card_suit = self.SUIT_MAP[card[1]]
                state_vector.extend([card_val, card_suit])
            else:
                state_vector.extend([0, 0])

        for track_idx in range(3):
            state_vector.append(player_board.get_track_score(track_idx))

        for track_idx in range(3):
            state_vector.append(opponent_board.get_track_score(track_idx))

        for track_idx in range(3):
            raw_dir = player_board.directions[track_idx]
            state_vector.append(self.DIRECTION_MAP.get(raw_dir, 0))

        return np.array(state_vector, dtype=np.int32)

    def _draw_replacement(self, hand, deck):
        new_card = deck.draw()
        if new_card is not None:
            hand.cards.append(new_card)

    def _apply_discard(self, hand, deck, hand_slot: int):
        if not (0 <= hand_slot < len(hand.cards)):
            return False

        hand.cards.pop(hand_slot)
        self._draw_replacement(hand, deck)
        return True

    def _apply_disband(self, board, track_index: int):
        return board.discard_track(track_index)

    def _apply_play(self, hand, hand_slot: int, target_track: int, own_board, enemy_board, deck):
        if not (0 <= hand_slot < len(hand.cards)):
            return False, 0.0

        card = hand.cards[hand_slot]
        is_face_card = card[0] in ["Jack", "Queen", "King"]

        if target_track < 3:
            if is_face_card:
                if not self._face_card_can_target_top(own_board, target_track):
                    return False, 0.0
                if not own_board.add_face_to_card(target_track, len(own_board.tracks[target_track]) - 1, card):
                    return False, 0.0
            else:
                if not own_board.add_to_track(target_track, card):
                    return False, 0.0

            hand.cards.pop(hand_slot)
            self._draw_replacement(hand, deck)

            current_score = own_board.get_track_score(target_track)
            if 21 <= current_score <= 26:
                return True, 2.0
            if current_score > 26:
                return True, -2.0
            return True, 0.1

        opponent_track_index = target_track - 3
        if not is_face_card:
            return False, 0.0
        if not self._face_card_can_target_top(enemy_board, opponent_track_index):
            return False, 0.0
        if not enemy_board.add_face_to_card(opponent_track_index, len(enemy_board.tracks[opponent_track_index]) - 1, card):
            return False, 0.0

        hand.cards.pop(hand_slot)
        self._draw_replacement(hand, deck)

        opponent_score = enemy_board.get_track_score(opponent_track_index)
        if opponent_score > 26:
            return True, 3.0
        return True, 0.0

    def execute_opponent_turn(self):
        mask = self.get_action_mask(self.opponent_hand, self.opponent_board, self.player_board)
        legal_actions = np.flatnonzero(mask)
        if len(legal_actions) == 0:
            return

        action = int(random.choice(legal_actions))
        move = self.decode_action(action)

        if move["type"] == "discard":
            self._apply_discard(self.opponent_hand, self.opponent_deck, move["hand_slot"])
            return

        if move["type"] == "disband":
            self._apply_disband(self.opponent_board, move["track_index"])
            return

        if move["type"] == "play":
            self._apply_play(
                self.opponent_hand,
                move["hand_slot"],
                move["target_track"],
                self.opponent_board,
                self.player_board,
                self.opponent_deck,
            )

    def check_game_over(self):
        player_cards_left = len(self.player_hand.cards) + self.player_deck.cards_left()
        opponent_cards_left = len(self.opponent_hand.cards) + self.opponent_deck.cards_left()

        if player_cards_left == 0 and opponent_cards_left == 0:
            self.player_won = False
            self.opponent_won = False
            return True
        if player_cards_left == 0:
            self.player_won = False
            self.opponent_won = True
            return True
        if opponent_cards_left == 0:
            self.player_won = True
            self.opponent_won = False
            return True

        p1_ready = [21 <= self.player_board.get_track_score(i) <= 26 for i in range(3)]
        p2_ready = [21 <= self.opponent_board.get_track_score(i) <= 26 for i in range(3)]

        player_track_wins = 0
        opponent_track_wins = 0

        # Caravan Rule: Every single column slot must have at least one sold caravan
        for i in range(3):
            # If neither player has a caravan between 21 and 26 in this slot, the game CANNOT end
            if not p1_ready[i] and not p2_ready[i]:
                return False

            p1_score = self.player_board.get_track_score(i)
            p2_score = self.opponent_board.get_track_score(i)

            # Assign track victories safely without breaking the outer loop on ties
            if p1_ready[i] and (not p2_ready[i] or p1_score > p2_score):
                player_track_wins += 1
            elif p2_ready[i] and (not p1_ready[i] or p2_score > p1_score):
                opponent_track_wins += 1
            # If p1_score == p2_score, it's a tie for this slot. Neither increments their win counter.

        # If the code reaches here, it means all 3 track columns are fully built and paired up!
        if player_track_wins > opponent_track_wins:
            self.player_won = True
            self.opponent_won = False
        elif opponent_track_wins > player_track_wins:
            self.player_won = False
            self.opponent_won = True
        else:
            # Absolute tie game across the whole board
            self.player_won = False
            self.opponent_won = False
            
        return True

    def step(self, action: int):
        move = self.decode_action(action)
        reward = 0.0

        if self.terminated:
            observation = self.encode_state(self.player_hand, self.player_board, self.opponent_board)
            info = {"action_mask": self.get_action_mask(self.player_hand, self.player_board, self.opponent_board)}
            return observation, reward, True, False, info

        mask = self.get_action_mask(self.player_hand, self.player_board, self.opponent_board)
        if action < 0 or action >= len(mask) or not mask[action]:
            reward -= 1.0
            observation = self.encode_state(self.player_hand, self.player_board, self.opponent_board)
            info = {"action_mask": mask}
            return observation, reward, False, False, info

        if move["type"] == "discard":
            if self._apply_discard(self.player_hand, self.player_deck, move["hand_slot"]):
                reward += 0.1
            else:
                reward -= 1.0

        elif move["type"] == "disband":
            if self._apply_disband(self.player_board, move["track_index"]):
                reward -= 0.5
            else:
                reward -= 1.0

        elif move["type"] == "play":
            success, play_reward = self._apply_play(
                self.player_hand,
                move["hand_slot"],
                move["target_track"],
                self.player_board,
                self.opponent_board,
                self.player_deck,
            )
            if success:
                reward += play_reward
            else:
                reward -= 1.0

        self.execute_opponent_turn()
        self.terminated = self.check_game_over()

        if self.terminated and self.player_won:
            reward += 20.0
        elif self.terminated and self.opponent_won:
            reward -= 20.0

        observation = self.encode_state(self.player_hand, self.player_board, self.opponent_board)
        info = {"action_mask": self.get_action_mask(self.player_hand, self.player_board, self.opponent_board)}
        
        # This return must be reached in all standard paths!
        return observation, reward, self.terminated, False, info