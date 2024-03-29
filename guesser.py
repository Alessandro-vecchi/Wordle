import numpy as np
import os, re
from scipy.stats import entropy
import itertools as it
import yaml
from rich.console import Console

from matrix_generator import PatternMatrixGenerator



class Guesser:
    """A class to guess words in a Wordle-like game."""

    DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data")
    WORD_LIST = os.path.join(DATA_DIR, "wordlist.yaml")

    def __init__(self, manual):
        """Initialize the Guesser with a word list and setup for manual or automated guessing."""
        self.word_list = self.get_word_list(isTrain=True) # 4270 if True; 2315 if False

        self._manual = manual
        self.console = Console()  # Console object for interactive output

        self._tried = []
        self.target_words = self.word_list

        # Initialize PatternMatrixGenerator and load or generate the pattern matrix
        self.pattern_matrix_generator = PatternMatrixGenerator(self.word_list)
        self.pattern_matrix_generator.get_pattern_matrix(self.word_list, self.word_list)


    def get_word_list(self, isTrain = True):
        """Get the word list """
        if isTrain:
            return yaml.load(open(self.WORD_LIST), Loader=yaml.FullLoader)
        return open('data/wordle_list.txt').read().splitlines()
    

    def restart_game(self, do_print = True):
        """Reset the game state for a new game."""
        if do_print:
            self.console.print("[bold cyan]Game restarted! New word set loaded.[/bold cyan]")
        self._tried = []
        self.target_words = self.word_list

    def get_guess(self, result, do_print = True):
        """Get the next guess based on the game state and previous result."""
        if self._manual == 'manual':
            # In manual mode, prompt the user for their guess
            return self.console.input('Your guess:\n')
        # In automated mode, use the fixed first guess or calculate the best next guess
        #first_guess = None
        guess = self.get_best_guess(result, do_print)
        self._tried.append(guess)
        return guess

    def get_best_guess(self, result, do_print = True, first_guess = "sound"):
        """Determine the best next guess based on the current game state and previous result."""
        if not self._tried and first_guess is not None:
            # For the first guess, use a fixed word to ensure consistent results
            return first_guess
        
        if self._tried:
            # Filter the current possible words based on the last result and exclude tried words
            self.target_words = self.filter_words(result)

        # Calculate the information value (entropy) for each possible word
        information_dic = self.get_entropies()
        
        # First, sort by presence in self.target_words (True before False), then by entropy (decreasing)
        word_entropy_pairs = sorted(information_dic.items(), 
                                    key=lambda item: (-item[1], item[0] not in self.target_words))

        
        if not self.target_words:
            raise ValueError("No words available. The word may not be present in the word list.")
        
        # Select the word with the maximum entropy as the best guess
        max_entropy_word = word_entropy_pairs[0][0]

        if do_print:
            self.print_top_information_values(word_entropy_pairs)
            self.print_max_entropy_word(max_entropy_word, information_dic[max_entropy_word])

        return max_entropy_word

    def filter_words(self, result):
        """Filter the current possible words based on the feedback pattern from the last guess."""
        pattern = self.build_regex(result)
        
        regex = re.compile(pattern)
        
        return [word for word in self.target_words if regex.match(word)]
    

    def build_regex(self, feedback_pattern):
        """Construct a regex pattern to match words based on feedback, handling complex cases like correct, misplaced, and absent letters.
        
        Args:
            feedback_pattern (str): Feedback from the previous guess (e.g., '+--ie') indicating correct ('e'), misplaced ('-'), and absent ('+') letters.
        """
        # The previous guess made by the Guesser
        previous_guess = self._tried[-1]  # Example: 'eerie'

        # Mapping each letter in the previous guess to its feedback
        letter_feedback_mapping = {letter: [] for letter in previous_guess}  # Initializes mapping for each unique letter. Example: {'e': [], 'r': [], 'i': []}

        # Populate the mapping with feedback for each letter. Example: {'e': ['+', '-', 'e'], 'r': ['-'], 'i': ['+']}
        for guess_letter, feedback_letter in zip(previous_guess, feedback_pattern):
            if not (feedback_letter == '+' and feedback_letter in letter_feedback_mapping[guess_letter]):
                letter_feedback_mapping[guess_letter].append(feedback_letter)

        # Determine letters that are misplaced
        misplaced_letters = {l for pattern, l in zip(feedback_pattern, previous_guess) if pattern == '-'} # Example: {'r', 'e'}

        # Identify incorrect letters, ensuring no duplication by using a set
        excluded_letters = "".join({l for p, l in zip(feedback_pattern, previous_guess) if p == '+' and l not in misplaced_letters}) # Example: 'i'

        # Initialize the main regex pattern
        pattern = ''

        # Construct the main pattern based on feedback
        for i in range(5): # Example: [('e', '+'), ('e', '-'), ('r', '-'), ('i', '+'), ('e', '-')]
            previous_guess_char, feedback_char = previous_guess[i], feedback_pattern[i]
            feedback_regex = ''
            if feedback_char.isalpha():
                # Directly append correct letters
                feedback_regex += feedback_char

            elif feedback_char == '+':
                # If the letter is incorrect, exclude it from the pattern
                ex = set(excluded_letters) | set(previous_guess_char) # if previous_guess_char in excluded_letters else previous_guess_char+excluded_letters
                feedback_regex += f'[^{"".join(ex)}]' # Example: '[^eir]'

            elif feedback_char == '-':
                # If the letter is misplaced, in addition to excluding the wrong letters also exclude the misplaced one
                feedback_regex += f'[^{excluded_letters + previous_guess_char}]' # Example: '[^eir]'


            pattern += feedback_regex

        # Begin constructing the lookahead expressions
        lookaheads = '^'

        # Process each letter in the mapping to construct lookaheads ensuring correct letter count and placement
        for letter, feedback_values in letter_feedback_mapping.items():
            feedback_length = len(feedback_values)
            if feedback_length > 1:
                incorrect_count = feedback_values.count('+')
                min_count = feedback_length - incorrect_count
                max_count = "" if incorrect_count > 0 else ","  # Max possible count of any letter in a 5-letter word
                lookaheads += f'(?=(?:[^{letter}]*{letter}[^{letter}]*){{{min_count}{max_count}}}$)'
            elif feedback_values == ['-']:
                # Ensure the letter appears at least once if it's misplaced
                lookaheads += f'(?=.*{letter})'

        # Combine lookaheads and the main pattern to form the full regex pattern
        full_pattern = lookaheads + pattern + "$"
        #print(full_pattern)
        return full_pattern
    

    def get_entropies(self):
        """Calculate the entropy for each possible word"""
        # Get patterns for all possible words against current target words
        pattern_matrix = self.pattern_matrix_generator.get_pattern_matrix(self.word_list, self.target_words)

        # Calculate the probabilities for each pattern in each word
        probabilities = self.get_probabilities(pattern_matrix)

        # Calculate the entropy for each distribution
        information_values_array = self.entropy_of_distributions(probabilities)

        # Map the entropy values back to the corresponding words
        information_values = dict(zip(self.word_list, information_values_array))

        return information_values
    
    
    def get_probabilities(self, pattern_matrix):
        # Initialize the distributions matrix
        # Each row corresponds to a guess, and each column to a possible pattern (3^5 total patterns)
        probabilities = np.zeros((len(self.word_list), 3**5))

        # Fill the distributions matrix using advanced indexing
        row_indices = np.arange(len(self.word_list))
        # Use pattern_matrix as column indices to increment counts for corresponding patterns
        np.add.at(probabilities, (row_indices[:, None], pattern_matrix), 1)

        # Convert counts to probabilities
        probabilities /= len(self.target_words)

        return probabilities

    
    @staticmethod
    def entropy_of_distributions(distributions):
        return entropy(distributions, base=2, axis=1)

    
    def print_top_information_values(self, information_values, n=10):
        """Prints the top n words with their corresponding information values."""
        
        top_10_information_values = information_values[:n]
        
        self.console.print(f"Top {min(n, len(top_10_information_values))} Words and their Information Values:")
        for word, value in top_10_information_values:
            self.console.print(f"{word}: {value:.4f}")

    def print_max_entropy_word(self, word, entropy):
        """Print the word with the maximum entropy before making a guess."""
        self.console.print(f"Next Guess (Max Entropy): [bold]{word}[/bold] with entropy [bold]{entropy:.4f}[/bold]")
        self.console.print(f"Total Possible Words: {len(self.target_words)}")

    @staticmethod
    def pattern_to_int_list(pattern):
        result = []
        curr = pattern
        for _ in range(5):
            result.append(curr % 3)
            curr = curr // 3
        return result

    def pattern_to_string(self, pattern):
        d = {0: "+", 1: "-", 2: "l"}
        return "".join(d[x] for x in self.pattern_to_int_list(pattern))
    
    @staticmethod
    def information(probabilities):
        """Calculate the entropy (information value) for a set of probabilities.
        
        Args:
            probabilities (np.ndarray): Array of probabilities for each possible outcome. Dimensions: (len(words), 243)."""
        probabilities = probabilities[probabilities > 0]
        return -np.sum(probabilities * np.log2(probabilities), axis=1)



