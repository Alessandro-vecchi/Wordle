from wordle import Wordle
from guesser import Guesser
from guesserfreq import GuesserFreq
from avg_3_62 import Guesser2
import argparse, os
import cProfile
import pstats
import subprocess
import matplotlib.pyplot as plt, numpy as np


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
            print(" " + "-"*4 + f"Guess {guesses}" + "-"*25+" ")
            guess = guesser.get_guess(result)
            result, endgame = wordle.check_guess(guess)    
            # print(result)
        return result, guesses
            

def run_games_with_profiling(run_games_func):
    """Run the games with profiling, and visualize results using snakeviz."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    run_games_func()  # Run the actual game function
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.dump_stats('profile_results.prof')  # Save stats for visualization
    
    # Use subprocess to launch snakeviz
    subprocess.run(['snakeviz', 'profile_results.prof'])

def run_games_without_profiling(run_games_func):
    """Run the games without profiling."""
    run_games_func()

def save_guesses_histogram(g, filename='guesses_distribution.png'):
    DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "plot",
    )
    fullpath = os.path.join(DIR, filename)
    # Calculate the distribution of guesses
    max_guess = max(g)
    min_guess = min(g)
    bins = np.arange(min_guess, max_guess + 2) - 0.5  # Set bins edges
    hist, _ = np.histogram(g, bins=bins)

    # Calculate the average number of guesses
    avg_guesses = np.mean(g)
    avg_line = np.full(len(hist), avg_guesses)

    # Create the histogram plot
    plt.figure(figsize=(10, 6))
    plt.hist(g, bins=bins, alpha=0.7, label='Number of Guesses', color='skyblue', edgecolor='black')
    plt.plot(range(min_guess, max_guess + 1), avg_line, label=f'Average Guesses: {avg_guesses:.2f}', linestyle='--', color='red')

    # Customize the plot
    plt.title('Distribution of Guesses in Wordle-like Game')
    plt.xlabel('Number of Guesses')
    plt.ylabel('Frequency')
    plt.xticks(range(min_guess, max_guess + 1))
    plt.legend()

    # Save the plot to a file
    plt.grid(axis='y', alpha=0.75)
    plt.savefig(fullpath)
    plt.close()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--r', type=int)
    parser.add_argument('--profile', action='store_true', help='Enable profiling with snakeviz visualization')
    parser.add_argument('--save', type=str, action='save data', help='Save histogram plot of guesses distribution to a file.')
    args = parser.parse_args()
    if args.r:
        wordle = Wordle()
        guesser = Guesser('console')
        
        def run_games():
            for run in range(args.r):
                if run > 0:
                    guesser.restart_game()
                    wordle.restart_game()

                print(f"* ------- Run: {run} ------------- *")


                
                results, guesses = Game.game(wordle, guesser)
                Game.score(results, guesses)

        # Continue with the summary calculation and printing
        success_rate = RESULTS.count(True) / len(RESULTS) * 100
        print("\n\n---- Game Summary ----")
        print(f"Total number of games played: {args.r}")
        print(f"You correctly guessed {success_rate:.2f}% of words.")
        if GUESSES:
            avg_guesses = sum(GUESSES) / len(GUESSES)
            print(f"Average number of guesses: {avg_guesses:.2f}")
        
        if args.save:
            save_guesses_histogram(GUESSES, file=args.save)
        

        # Decide whether to profile based on the '--profile' command-line argument
        if args.profile:
            run_games_with_profiling(run_games)
        else:
            run_games_without_profiling(run_games)
    else:
        # For manual play, profiling might not be as relevant
        guesser = Guesser('manual')
        wordle = Wordle()
        print('Welcome! Let\'s play wordle! ')
        Game.game(wordle, guesser)

    