import sys
from wordle import Wordle
from guesser import Guesser
from guesserfreq import GuesserFreq
import argparse


class Game:
    global RESULTS, GUESSES
    GUESSES = [] # number of guesses per game
    RESULTS = [] # was the word guessed?
        
    def score(result, guesses):
        if '-' in result or '+' in result:
            # word was not guessed
            RESULTS.append(False)
        else:
            RESULTS.append(True)
            GUESSES.append(guesses)




    def game(wordle, guesser):
        endgame = False
        guesses = 0
        result = None
        while not endgame:
            guesses += 1
            print(" ")
            print("* " + "-"*4 + f"Guess {guesses}" + "-"*25+" *")
            guess = guesser.get_guess(result)
            result, endgame = wordle.check_guess(guess)    
            # print(result)
        return result, guesses
            
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--r', type=int)
    args = parser.parse_args()
    if args.r:
        successes = []
        wordle = Wordle()
        guesser = Guesser('console')
        for run in range(args.r):
            if run > 0:
                guesser.restart_game()
                wordle.restart_game()

            results, guesses = Game.game(wordle, guesser)
            Game.score(results, guesses)
        success_rate = RESULTS.count(True) / len(RESULTS) * 100
        

        print("\n\n---- Game Summary ----")
        print(f"Total number of games played: {args.r}")
        print(f"You correctly guessed {success_rate:.2f}% of words.")
        if GUESSES:
            avg_guesses = sum(GUESSES) / len(GUESSES)
            print(f"Average number of guesses: {avg_guesses:.2f}")
    else:
        # Play manually on console
        guesser = Guesser('manual')
        wordle = Wordle()
        print('Welcome! Let\'s play wordle! ')
        Game.game(wordle, guesser)
    