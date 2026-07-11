import random

class CaravanDeck:
    def __init__(self):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        values = ['Ace', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King']
        full_pool = [(value, suit) for suit in suits for value in values]
        
        self.cards = full_pool[:35]

        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)
    
    def draw(self):
        if len(self.cards) == 0:
            return None
        return self.cards.pop(0)
    
    def cards_left(self):
        return len(self.cards)

class PlayerHand:
    def __init__(self):
        self.cards = []

    def draw_initial_hand(self, deck):
        for _ in range(8):
            card = deck.draw()
            if card:
                self.cards.append(card)

    def play_or_discard(self, card_index, deck):
        if 0 <= card_index < len(self.cards):
            discarded_card = self.cards.pop(card_index)

            new_card = deck.draw()
            if new_card:
                self.cards.append(new_card)

            return discarded_card
        else:
            raise IndexError("Card index out of range.")

    def show_hand(self):
        return self.cards

if __name__ == "__main__":
    deck = CaravanDeck()
    player_hand = PlayerHand()
    player_hand.draw_initial_hand(deck)

    print("Initial hand:", player_hand.show_hand())

    played_card = player_hand.play_or_discard(0, deck)
    print(f"AI played card: {played_card}")
    print(f"New hand after playing card: {player_hand.show_hand()}")
    print(f"Cards left in deck: {deck.cards_left()}")