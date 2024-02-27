from wordle import Wordle
from guesser import Guesser
from guesserfreq import GuesserFreq
from avg_3_62 import Guesser2
import argparse, os
import cProfile
import pstats
import subprocess
import contextlib
import matplotlib.pyplot as plt, numpy as np
from tqdm import tqdm


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




    def game(wordle, guesser, do_print=True):
        endgame = False
        guesses = 0
        result = None
        while not endgame:
            guesses += 1
            if do_print:
                print("\n " + "-"*4 + f"Guess {guesses}" + "-"*25+" ")
            guess = guesser.get_guess(result, do_print)
            result, endgame = wordle.check_guess(guess, do_print)    
            # print(result)
        return result, guesses
            

@contextlib.contextmanager
def managed_subprocess(*args, **kwargs):
    process = subprocess.Popen(*args, **kwargs)
    try:
        yield process
    finally:
        process.terminate()

def run_games_with_profiling(run_games_func):
    """Run the games with profiling, and visualize results using snakeviz."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    run_games_func()  # Run the actual game function
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.dump_stats('profile_results.prof')  # Save stats for visualization
    
    # Automatically close the snakeviz subprocess
    with managed_subprocess(['snakeviz', 'profile_results.prof']):
        input("Press Enter to close snakeviz...")  # Wait for user input to proceed


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


# python3 game.py --r 300 --profile --save guesses_distribution.png
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--r', type=int)
    parser.add_argument('--profile', action='store_true', help='Enable profiling with snakeviz visualization')
    parser.add_argument('--save', type=str, help='Save histogram plot of guesses distribution to a file.')
    parser.add_argument('--print', action="store_true", help='Enable print of the game.')
    args = parser.parse_args()
    if args.r:
        wordle = Wordle()
        guesser = Guesser('console')

        def run_games():
            n = range(args.r) if args.print else tqdm(range(args.r), desc="Running Games", unit="game")
            for run in n:
                if run > 0:
                    guesser.restart_game(args.print)
                    wordle.restart_game()

                if args.print:
                    print(f"* ------- Run: {run} ------------- *")



                
                results, guesses = Game.game(wordle, guesser, args.print)
                Game.score(results, guesses)

        # Decide whether to profile based on the '--profile' command-line argument
        if args.profile:
            run_games_with_profiling(run_games)
        else:
            run_games_without_profiling(run_games)
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
        
        if args.profile:
            # Use subprocess to launch snakeviz
            subprocess.run(['snakeviz', 'profile_results.prof'])

    else:
        # For manual play, profiling might not be as relevant
        guesser = Guesser('manual')
        wordle = Wordle()
        print('Welcome! Let\'s play wordle! ')
        Game.game(wordle, guesser)

    