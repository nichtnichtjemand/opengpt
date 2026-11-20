#!/usr/bin/env python3
"""Simple Rock‑Paper‑Scissors command line game.

The player enters "rock", "paper" or "scissors" (case‑insensitive).
The computer chooses randomly, the winner is announced and the
player can decide to play another round.

Run the game with:
    python3 my_game/main.py
"""

import random
import sys

OPTIONS = ["rock", "paper", "scissors"]
WIN_MAP = {
    "rock": "scissors",
    "paper": "rock",
    "scissors": "paper",
}

def get_player_choice() -> str:
    while True:
        choice = input("Choose rock, paper or scissors (or 'quit' to exit): ")
        if choice.lower() == "quit":
            print("Thanks for playing! Bye.")
            sys.exit(0)
        if choice.lower() in OPTIONS:
            return choice.lower()
        print("Invalid choice, try again.")

def get_computer_choice() -> str:
    return random.choice(OPTIONS)

def decide_winner(player: str, computer: str) -> str:
    if player == computer:
        return "draw"
    elif WIN_MAP[player] == computer:
        return "player"
    else:
        return "computer"

def main() -> None:
    print("Welcome to Rock‑Paper‑Scissors!")
    while True:
        player = get_player_choice()
        computer = get_computer_choice()
        print(f"You chose {player}, computer chose {computer}.")
        result = decide_winner(player, computer)
        if result == "draw":
            print("It's a draw!")
        elif result == "player":
            print("You win! 🎉")
        else:
            print("Computer wins! 😞")
        # Loop continues; player can type 'quit' to exit.

if __name__ == "__main__":
    main()
