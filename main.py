import sys
from colorama import Fore, Style, init
from caravan_game import CaravanDeck, PlayerHand, CaravanTracks

# Initialize colorama for cross-platform terminal colors
init(autoreset=True)

FACE_CARDS = {'Jack', 'Queen', 'King'}


def prompt_face_target(current_turn, p1_board, p2_board, color):
    """Prompt for target owner/track for a face-card play."""
    own_board = p1_board if current_turn == 1 else p2_board
    opp_board = p2_board if current_turn == 1 else p1_board

    while True:
        owner_choice = input(f"{color}Target board (1=Yours, 2=Opponent): ").strip()
        if owner_choice == '1':
            target_board = own_board
            owner_name = 'your'
        elif owner_choice == '2':
            target_board = opp_board
            owner_name = "opponent's"
        else:
            print(Fore.RED + 'Invalid choice. Enter 1 or 2.')
            continue

        if sum(len(track) for track in target_board.tracks) == 0:
            print(Fore.RED + f"No cards on {owner_name} board to target.")
            continue

        track_choice = input(f"{color}Select target track on {owner_name} board (1-3): ").strip()
        if not track_choice.isdigit():
            print(Fore.RED + 'Invalid track selection. Choose 1, 2, or 3.')
            continue

        track_idx = int(track_choice) - 1
        if not (0 <= track_idx < 3):
            print(Fore.RED + 'Invalid track selection. Choose 1, 2, or 3.')
            continue

        target_track = target_board.tracks[track_idx]
        if not target_track:
            print(Fore.RED + 'That track is empty. Choose a non-empty track.')
            continue

        target_card_idx = len(target_track) - 1
        top_card = target_track[target_card_idx]
        print(f"{Fore.YELLOW}Targeting top card on Track {track_idx + 1}: {top_card[0]} of {top_card[1]}")

        return target_board, track_idx, target_card_idx

def print_board(p1_tracks, p2_tracks):
    """Prints the current score and the full stack of cards for both players side-by-side."""
    print(f"\n{Fore.YELLOW}=== CURRENT BOARD STATE ===")
    print(f"{Fore.GREEN}Player 1 (Card Stacks)                  {Fore.BLUE}Player 2 (Card Stacks)")
    print("-" * 80)
    
    for i in range(3):
        # Format Player 1 Track Info
        p1_score = p1_tracks.get_track_score(i)
        p1_track = p1_tracks.tracks[i]
        # Build string of the entire stack of cards
        p1_stack = " -> ".join([f"{c[0]} of {c[1]}" for c in p1_track]) if p1_track else "Empty"
        p1_dir = f" ({p1_tracks.directions[i]})" if p1_tracks.directions[i] else ""
        p1_str = f"Track {i+1} [Score: {p1_score:>2}]{p1_dir}: {p1_stack}"

        # Format Player 2 Track Info
        p2_score = p2_tracks.get_track_score(i)
        p2_track = p2_tracks.tracks[i]
        # Build string of the entire stack of cards
        p2_stack = " -> ".join([f"{c[0]} of {c[1]}" for c in p2_track]) if p2_track else "Empty"
        p2_dir = f" ({p2_tracks.directions[i]})" if p2_tracks.directions[i] else ""
        p2_str = f"Track {i+1} [Score: {p2_score:>2}]{p2_dir}: {p2_stack}"
        
        # Expanded padding to avoid clipping when stacks get long
        print(f"{Fore.GREEN}{p1_str:<45} {Fore.BLUE}{p2_str}")
    print(f"{Fore.YELLOW}===========================\n")

def check_win_condition(p1_tracks, p2_tracks):
    """
    Checks if the game has ended.
    - Track scoring is live when a side has 21-26 (inclusive).
    - A track is won by the side with the higher valid score, or by default if only one side is valid.
    - Match ends when all 3 tracks have winners; side with most track wins wins.
    """
    p1_ready = [21 <= p1_tracks.get_track_score(i) <= 26 for i in range(3)]
    p2_ready = [21 <= p2_tracks.get_track_score(i) <= 26 for i in range(3)]

    p1_wins = 0
    p2_wins = 0
    all_tracks_resolved = True

    for i in range(3):
        if not (p1_ready[i] or p2_ready[i]):
            all_tracks_resolved = False
            continue

        s1 = p1_tracks.get_track_score(i)
        s2 = p2_tracks.get_track_score(i)

        if p1_ready[i] and (not p2_ready[i] or s1 > s2):
            p1_wins += 1
        elif p2_ready[i] and (not p1_ready[i] or s2 > s1):
            p2_wins += 1
        else:
            # Equal valid scores mean this track is still contested.
            all_tracks_resolved = False

    if all_tracks_resolved:
        if p1_wins > p2_wins:
            return "Player 1"
        elif p2_wins > p1_wins:
            return "Player 2"
        return "Draw"

    return None


def check_card_depletion(p1_hand, p1_deck, p2_hand, p2_deck):
    """Returns immediate winner if a side has no cards left in hand+deck."""
    p1_total_cards = len(p1_hand.cards) + p1_deck.cards_left()
    p2_total_cards = len(p2_hand.cards) + p2_deck.cards_left()

    if p1_total_cards == 0 and p2_total_cards == 0:
        return "Draw"
    if p1_total_cards == 0:
        return "Player 2"
    if p2_total_cards == 0:
        return "Player 1"
    return None

if __name__ == "__main__":
    
    print(Fore.MAGENTA + Style.BRIGHT + "\n----- Welcome to Caravan local Co-Op -----\n")

    # 1. Initialize Decks
    p1_deck = CaravanDeck()
    p2_deck = CaravanDeck()

    # 2. Initialize Hands & Draw Opening Cards
    p1_hand = PlayerHand()
    p1_hand.draw_initial_hand(p1_deck)
    
    p2_hand = PlayerHand()
    p2_hand.draw_initial_hand(p2_deck)

    # 3. Initialize Game Boards
    p1_board = CaravanTracks()
    p2_board = CaravanTracks()

    # Turn management variables
    current_turn = 1  # 1 for Player 1, 2 for Player 2
    game_running = True

    while game_running:
        print_board(p1_board, p2_board)
        
        # Assign pointers based on whose turn it is
        if current_turn == 1:
            color = Fore.GREEN
            name = "PLAYER 1"
            hand = p1_hand
            board = p1_board
            deck = p1_deck
        else:
            color = Fore.BLUE
            name = "PLAYER 2"
            hand = p2_hand
            board = p2_board
            deck = p2_deck

        print(f"{color}--- {name}'S TURN ---")
        print(f"Cards remaining in your deck pool: {deck.cards_left()}")
        print("Your current Hand:")

        for idx, card in enumerate(hand.cards):
            print(f" [{idx + 1}]: {card[0]} of {card[1]}")
            
        print(f"\n\n [d]: Discard a card from your hand")
        print(" [0]: Discard one of your own tracks")
        
        # Action selection sub-loop to handle bad inputs gracefully
        move_successful = False
        while not move_successful:
            try:
                choice = input(f"\n{color}Select a card index to play, 'd' to discard from hand, '0' to discard a track, or 'q' to quit: ").strip().lower()
                if choice == 'q':
                    print(Fore.RED + "\nGame aborted.")
                    sys.exit()

                if choice in {'d', '9'}:
                    if not hand.cards:
                        print(Fore.RED + "Your hand is empty; you cannot discard from hand.")
                        continue

                    discard_prompt = f"{color}Select card index to discard (1-{len(hand.cards)}): "
                    discard_choice_raw = input(discard_prompt).strip()
                    if not discard_choice_raw.isdigit():
                        print(Fore.RED + "Invalid hand index.")
                        continue

                    discard_choice = int(discard_choice_raw) - 1
                    if not (0 <= discard_choice < len(hand.cards)):
                        print(Fore.RED + "Invalid hand index.")
                        continue

                    removed = hand.cards.pop(discard_choice)
                    print(f"{Fore.YELLOW}Discarded {removed[0]} of {removed[1]}.")

                    new_card = deck.draw()
                    if new_card:
                        hand.cards.append(new_card)
                        print(f"{Fore.YELLOW}Drew {new_card[0]} of {new_card[1]}.")
                    else:
                        print(Fore.YELLOW + "Your deck is empty. No replacement card drawn.")

                    move_successful = True
                    continue

                if choice == '0':
                    track_choice = input(f"{color}Select your track to discard (1-3): ").strip()
                    if not track_choice.isdigit():
                        print(Fore.RED + "Invalid track selection. Choose 1, 2, or 3.")
                        continue

                    track_idx = int(track_choice) - 1
                    if not board.discard_track(track_idx):
                        print(Fore.RED + "Track discard failed. Choose a non-empty track from 1 to 3.")
                        continue

                    print(Fore.YELLOW + f"Discarded all cards from Track {track_idx + 1}.")
                    move_successful = True
                    continue
                    
                card_idx = int(choice) - 1
                
                if not (0 <= card_idx < len(hand.cards)):
                    print(Fore.RED + "Invalid index. Choose a card in your hand.")
                    continue
                
                # Fetch reference card copy without removing yet
                chosen_card = hand.cards[card_idx]
                chosen_value, _ = chosen_card

                if chosen_value in FACE_CARDS:
                    target_board, track_idx, target_card_idx = prompt_face_target(
                        current_turn, p1_board, p2_board, color
                    )

                    if target_board.add_face_to_card(track_idx, target_card_idx, chosen_card):
                        hand.cards.pop(card_idx)
                        print(
                            f"{Fore.LIGHTGREEN_EX}Success! Played {chosen_card[0]} of {chosen_card[1]} "
                            f"on target card #{target_card_idx + 1} in Track {track_idx + 1}"
                        )

                        new_card = deck.draw()
                        if new_card:
                            hand.cards.append(new_card)

                        move_successful = True
                    else:
                        print(Fore.RED + "❌ Could not apply face card to that target.")
                    continue

                # Opening phase: first three successful placements are forced to Tracks 1, 2, and 3.
                cards_on_board = sum(len(track) for track in board.tracks)
                if cards_on_board < 3:
                    track_idx = cards_on_board
                    print(f"{color}Opening phase: {chosen_card[0]} of {chosen_card[1]} must be placed on Track {track_idx + 1}.")
                else:
                    track_choice = input(f"{color}Select a track to place this card on (1-3): ").strip()
                    if not track_choice.isdigit():
                        print(Fore.RED + "Invalid track selection. Choose 1, 2, or 3.")
                        continue

                    track_idx = int(track_choice) - 1
                    if not (0 <= track_idx < 3):
                        print(Fore.RED + "Invalid track selection. Choose 1, 2, or 3.")
                        continue
                
                # Run the action verification code
                if board.add_to_track(track_idx, chosen_card):
                    # Remove it from hand since it was accepted by the tracks object
                    hand.cards.pop(card_idx)
                    print(f"{Fore.LIGHTGREEN_EX}Success! Played {chosen_card[0]} of {chosen_card[1]} on Track {track_idx + 1}")
                    
                    # Draw a replacement card from the custom deck pool
                    new_card = deck.draw()
                    if new_card:
                        hand.cards.append(new_card)
                    
                    move_successful = True
                else:
                    print(Fore.RED + "❌ Move is illegal under Caravan rules! Try a different move or discard.")
                    
            except ValueError:
                print(Fore.RED + "Please enter valid numeric integers.")

        # Check if this turn triggered a game-winning condition.
        winner = check_card_depletion(p1_hand, p1_deck, p2_hand, p2_deck)
        if winner is None:
            winner = check_win_condition(p1_board, p2_board)

        if winner:
            print_board(p1_board, p2_board)
            if winner == "Draw":
                print(Fore.YELLOW + Style.BRIGHT + "Match over! It's a draw.")
            else:
                print(Fore.YELLOW + Style.BRIGHT + f"🎉 Match over! {winner} wins the Caravan round!")
            game_running = False
        else:
            # Alternate active turn states
            current_turn = 2 if current_turn == 1 else 1

    print(Fore.MAGENTA + "------ Game Complete ------")