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
