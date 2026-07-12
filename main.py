from colorama import Fore, Style

from caravan_game import CaravanDeck, PlayerHand, CaravanTracks

if __name__ == "__main__":
    print(Fore.GREEN)
    print('\n-----Starting Caravan Game-----\n')

    # Initialize the deck
    deck = CaravanDeck()
    print(f"Deck initialized with {deck.cards_left()} cards.")

    # 2. Intialize the player's hand and draw cards
    player_hand = PlayerHand()
    player_hand.draw_initial_hand(deck)
    
    print(f"Player draws 8 cards")
    for index, card in enumerate(player_hand.cards):
        print(f" Index {index + 1}: {card[0]} of {card[1]}")

    # initialize the game board
    board = CaravanTracks()

    # 4. Simulate playing the first card from Hand onto Track 1
    chosen_card = player_hand.cards.pop(0)
    board.add_to_track(0, chosen_card)
    print(f"\nSimulating turn: Played {chosen_card[0]} of {chosen_card[1]} onto Track 1")

    # 5. Show the current state of the board
    print("\nCurrent state of the board:")
    for i, track in enumerate(board.tracks):
        if track:
            print(f" Track {i + 1}: {track[-1][0]} of {track[-1][1]}")
        else:
            print(f" Track {i + 1}: Empty")
    
    print(f"\nCards left in deck: {deck.cards_left()}")
    print(f"------Test Complete------\n")
    print(Style.RESET_ALL)
