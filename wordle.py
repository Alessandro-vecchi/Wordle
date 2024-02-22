from random import choice
import yaml
from collections import Counter
from rich.console import Console
from rich.markup import escape

class Wordle:
    global ALLOWED_GUESSES, word_list
    ALLOWED_GUESSES = 6
    word_list = yaml.load(open('wordlist.yaml'), Loader=yaml.FullLoader)
    #word_list = open('wordle_list.txt').read().splitlines()

    def __init__(self):
        self._word = choice(word_list)
        #print(self._word)
        #self._word = "dirge"
        self._word = "gucci"
        self._tried = []
        self.console = Console()  # Console object for interactive output


    def restart_game(self):
        #ws = ["stare", "stale", "stake", "stave", "stage", "stale"]
        self._word = choice(word_list)
        print(self._word)
        self._tried = []
        self._endgame = False


    def get_matches(self, guess):
        # Produces the feedback string
        counts = Counter(self._word)
        results = []
        for i, letter in enumerate(guess):
            if guess[i] == self._word[i]:
                results+=guess[i]
                counts[guess[i]]-=1
            else:
                results+='+'

        for i, letter in enumerate(guess):
            if guess[i] != self._word[i] and guess[i] in self._word:
                if counts[guess[i]]>0:
                    counts[guess[i]]-=1
                    results[i]='-'

        return ''.join(results)

    def check_guess(self, guess):
        result = False
        end_game = False
        guess = guess.lower().strip() # convert to lowercase and remove leading/trailing whitespace

        # check if the guess is valid
        if not guess.isalpha():
            return "Please enter only letters", False
        if len(guess) != 5:
            return "Please enter a five-letter word", False
        elif guess in self._tried:
            return "You have already tried that word", False
        else:
            self._tried.append(guess)
            if guess == self._word:
                end_game = True
                result = self._word
                print('Congratulations, you guessed the word!')
            else:
                result = self.get_matches(guess)
                if len(self._tried) == ALLOWED_GUESSES:
                    print('Sorry, you did not guess the word. The word was ', self._word)
                    end_game = True
            self.print_feedback_pattern(guess, result)
        
        return result, end_game
    
    def print_feedback_pattern(self, guess, result):
        """Print the feedback pattern in a visual way."""
        styled_guess = ""
        for g, r in zip(guess, result):
            if r.isalpha():
                # Correct letter
                styled_guess += f"[green]{g}[/green]"
            elif r == '-':
                # Misplaced letter
                styled_guess += f"[yellow]{g}[/yellow]"
            else:
                # Incorrect letter
                styled_guess += f"[red]{g}[/red]"
        self.console.print(f"Feedback for {escape(guess)}: {styled_guess}", style="bold")
