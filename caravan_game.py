import random

class CaravanDeck:
    def __init__(self, custom_card_pool=None):
        """Initializes a 35-card player deck pool optimal for RL training."""
        if custom_card_pool is not None:
            self.cards = list(custom_card_pool)
        else:
            suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
            values = ['Ace', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King']
            
            # 1. Scramble the basic building blocks first
            random.shuffle(values)
            random.shuffle(suits)
            
            # 2. Build the master deck from the scrambled parts
            master_pool = [(v, s) for s in suits for v in values] * 10
            
            # 3. Scramble the combined pool completely
            random.shuffle(master_pool)
            
            # 4. Grab your 35 random cards
            self.cards = random.sample(master_pool, 500)
        
        # 5. Final pass shuffle on the active deck instance
        random.shuffle(self.cards)
        
    def draw(self):
        if self.cards:
            return self.cards.pop()
        return None
    
    def cards_left(self) -> int:
        return len(self.cards)

class PlayerHand:
    def __init__(self):
        self.cards = []
        
    def draw_initial_hand(self, deck):
        """Draws 8 initial cards out of the 35 available in the deck."""
        while len(self.cards) < 8:
            card = deck.draw()
            if card:
                self.cards.append(card)
            else:
                break

class CaravanTracks:
    def __init__(self):
        # Create 3 empty tracks for the player
        self.tracks = [[], [], []]
        # Track the active numerical direction flow for each caravan column
        self.directions = [None, None, None]
        # Track the active override suit (changed when a Queen is played)
        self.track_suits = [None, None, None]
    
    def get_track_score(self, track_index: int) -> int:
        """Calculates point totals while processing Kings dynamically."""
        track = self.tracks[track_index]
        card_weight = {
            'Ace': 1, '2': 2, '3': 3, '4': 4, '5': 5, 
            '6': 6, '7': 7, '8': 8, '9': 9, '10': 10
        }
        
        resolved_cards = []
        for card in track:
            value, suit = card
            if value in card_weight:
                resolved_cards.append([card_weight[value], 1])
            elif value == 'King' and resolved_cards:
                resolved_cards[-1][1] *= 2
                
        return sum(base * multiplier for base, multiplier in resolved_cards)

    def _recompute_track_state(self, track_index: int):
        """Rebuild direction and Queen suit override from cards present on a track."""
        track = self.tracks[track_index]

        self.directions[track_index] = None
        self.track_suits[track_index] = None

        first_number_weight = None

        for value, suit in track:
            if value in ['Jack', 'Queen', 'King']:
                if value == 'Queen':
                    self.track_suits[track_index] = suit
                    if self.directions[track_index] is not None:
                        self.directions[track_index] = 'Desc' if self.directions[track_index] == 'Asc' else 'Asc'
                continue

            current_weight = 1 if value == 'Ace' else int(value)

            if first_number_weight is None:
                first_number_weight = current_weight
            elif self.directions[track_index] is None and current_weight != first_number_weight:
                self.directions[track_index] = 'Asc' if current_weight > first_number_weight else 'Desc'

    def add_face_to_card(self, track_index: int, target_card_index: int, face_card: tuple) -> bool:
        """Attach a face card to a specific existing card on this track."""
        if not (0 <= track_index < 3):
            return False

        value, _ = face_card
        if value not in ['Jack', 'Queen', 'King']:
            return False

        track = self.tracks[track_index]
        if not (0 <= target_card_index < len(track)):
            return False

        if target_card_index != len(track) - 1:
            # Face cards can only be played onto the current top card of a track.
            return False

        if value == 'Jack':
            # Jack removes the targeted top card.
            del track[target_card_index:]
        else:
            track.insert(target_card_index + 1, face_card)

        self._recompute_track_state(track_index)
        return True

    def is_legal_move(self, track_index: int, card: tuple) -> bool:
        """Pure side-effect-free validation check for move choices."""
        track = self.tracks[track_index]
        value, suit = card

        # Face cards can target any existing card on a track
        if value in ['Jack', 'Queen', 'King']:
            return len(track) > 0  
        
        # Empty tracks can accept any number card or Ace
        if not track:
            return True
        
        def card_weight(val):
            return 1 if val == 'Ace' else int(val)

        last_numeric_card = None
        for existing_card in reversed(track):
            if existing_card[0] not in ['Jack', 'Queen', 'King']:
                last_numeric_card = existing_card
                break

        if last_numeric_card is None:
            return True

        last_card_value, last_card_suit = last_numeric_card

        current_weight = card_weight(value)
        last_weight = card_weight(last_card_value)

        # Cannot place identical consecutive numbers on the same track
        if current_weight == last_weight:
            return False
        
        # Second card placement is always legal and establishes direction
        if len(track) == 1:
            return True
        
        # Check suit override (Queens) or fallback to standard last card suit
        active_suit = self.track_suits[track_index] if self.track_suits[track_index] else last_card_suit
        if suit == active_suit:
            return True 
        
        # Enforce direction constraints
        direction = self.directions[track_index]
        if direction == 'Asc' and current_weight > last_weight:
            return True
        elif direction == 'Desc' and current_weight < last_weight:
            return True
        
        return False

    def add_to_track(self, track_index: int, card: tuple) -> bool:
        """Validates first, appends, and manages Queen direction flips."""
        if not (0 <= track_index < 3) or not self.is_legal_move(track_index, card):
            return False
            
        track = self.tracks[track_index]
        value, suit = card
        
        track.append(card)
        self._recompute_track_state(track_index)
        return True

    def discard_track(self, track_index: int) -> bool:
        """Discard all cards from a chosen track."""
        if not (0 <= track_index < 3):
            return False

        if not self.tracks[track_index]:
            return False

        self.tracks[track_index].clear()
        self._recompute_track_state(track_index)
        return True

    def discard_card(self, track_index: int, card_index: int) -> bool:
        """Discard one chosen card from a track."""
        if not (0 <= track_index < 3):
            return False

        track = self.tracks[track_index]
        if not (0 <= card_index < len(track)):
            return False

        track.pop(card_index)
        self._recompute_track_state(track_index)
        return True