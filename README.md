# caravan-ai
an AI built for the caravan mini-game from the critically acclaimed Fallout: New Vegas


# AI Development

1. Start by creating an action space. This will contain the total actions possible by the AI agent. Each combination of move (eg. Card 1 from hand goes to track 3 of my own) will be a particular action (eg. Action 1), as neural networks reads in vector numbers to comprehend moves. 

Action Space: 

-> Actions 0 - 7 (8): Discard the card currently sitting in hand slot 0 - 7
-> Actions 8 - 10 (3): Disband your own Track, 0, 1 or 2
-> Actions 11 - 58 (48): Play card from Hand Slot X (0 - 7) onto Track Y (0-5). 3 tracks for you 3 tracks for your opponent

