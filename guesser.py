import numpy as np
import os, re
from collections import Counter
from scipy.stats import entropy
import itertools as it
import yaml
from rich.console import Console

from matrix_generator import PatternMatrixGenerator



class Guesser:
    """A class to guess words in a Wordle-like game."""
    # To store the large grid of patterns at run time
    PATTERN_GRID_DATA = dict()

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
        self.grid = self.pattern_matrix_generator.grid



    @staticmethod
    def get_word_list(isTrain = True):
        """Get the word list """
        if isTrain:
            return yaml.load(open('wordlist.yaml'), Loader=yaml.FullLoader)
        return open('wordle_list.txt').read().splitlines()
    

    def restart_game(self):
        """Reset the game state for a new game."""
        self.console.print("[bold cyan]Game restarted! New word set loaded.[/bold cyan]")
        self._tried = []
        self.target_words = self.word_list

    def get_guess(self, result):
        """Get the next guess based on the game state and previous result."""
        if self._manual == 'manual':
            # In manual mode, prompt the user for their guess
            return self.console.input('Your guess:\n')
        # In automated mode, use the fixed first guess or calculate the best next guess
        guess = self.get_best_guess(result)
        self._tried.append(guess)
        return guess

    def get_best_guess(self, result):
        """Determine the best next guess based on the current game state and previous result."""
        if not self._tried:
            # For the first guess, use a fixed word to ensure consistent results
            return "aires"
            #return "eerie"
            pass
        else:
            # Filter the current possible words based on the last result and exclude tried words
            self.target_words = self.filter_words(result)

        # print(self.target_words)
        # Calculate the information value (entropy) for each possible word
        information_dic = self.get_information_values_vectorized()
        
        # First, sort by presence in self.target_words (True before False), then by entropy (decreasing)
        word_entropy_pairs = sorted(information_dic.items(), 
                                    key=lambda item: (-item[1], item[0] not in self.target_words))

        # Print the top n words with their corresponding information values
        #self.print_top_information_values(word_entropy_pairs)
        
        # depth_2_search(pattern_counts, information_values)
        
        if not self.target_words:
            # If no information values are available, the word is not present in the word list
            raise ValueError("No information values available. The word may not be present in the word list.")
        
        # Select the word with the maximum entropy as the best guess
        max_entropy_word = word_entropy_pairs[0][0]
        #self.print_max_entropy_word(max_entropy_word, information_dic[max_entropy_word])

        return max_entropy_word

    def filter_words(self, result):
        """Filter the current possible words based on the feedback pattern from the last guess."""
        pattern = self.build_regex(result)
        #print(pattern)
        regex = re.compile(pattern)
        
        return [word for word in self.target_words if regex.match(word) and word != self._tried[-1]] # - set(self._tried)
    

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
    
    
    def get_information_value(self):
        """Calculate the information value (entropy) for each possible word based on the current pattern matrix."""
        l = len(self.target_words)
        # Get the pattern counts for all words
        pattern_matrix = self.pattern_matrix_generator.get_pattern_matrix(self.word_list, self.target_words)

        # Calculate the information value (entropy) for each word
        information_values_array = [self.information(np.unique(row, return_counts=True)[1] / l) for row in pattern_matrix]
        #information_values_array = [entropy(np.unique(row, return_counts=True)[1] / l, base=2) for row in pattern_matrix]

        # Convert the information values array to a dictionary with words as keys
        information_values = dict(zip(self.word_list, information_values_array))

        return information_values

    def get_information_values_vectorized(self):
        pattern_matrix = self.pattern_matrix_generator.get_pattern_matrix(self.word_list, self.target_words)
        l = len(self.target_words)  # Number of current words

        # Initialize the distributions matrix
        # Each row corresponds to a guess, and each column to a possible pattern (3^5 total patterns)
        distributions = np.zeros((len(self.word_list), 3**5))

        # Fill the distributions matrix using advanced indexing
        # np.arange(len(self.word_list)) creates an array [0, 1, ..., len(self.word_list)-1] for row indices
        row_indices = np.arange(len(self.word_list))
        # Use pattern_matrix as column indices to increment counts for corresponding patterns
        np.add.at(distributions, (row_indices[:, None], pattern_matrix), 1)

        # Convert counts to probabilities
        distributions /= l

        # Calculate the entropy for each distribution
        information_values_array = self.entropy_of_distributions(distributions)

        # Map the entropy values back to the corresponding words
        information_values = dict(zip(self.word_list, information_values_array))

        return information_values
    
    @staticmethod
    def entropy_of_distributions(distributions):
        axis = len(distributions.shape) - 1
        return entropy(distributions, base=2, axis=axis)

    
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
        for x in range(5):
            result.append(curr % 3)
            curr = curr // 3
        return result

    def pattern_to_string(self, pattern):
        d = {0: "+", 1: "-", 2: "l"}
        return "".join(d[x] for x in self.pattern_to_int_list(pattern))
    
    @staticmethod
    def information(probabilities):
        """Calculate the entropy (information value) for a set of probabilities."""
        return -np.sum(probabilities * np.log2(probabilities))



