import yaml, numpy as np, re
from rich.console import Console
from collections import Counter
# from string import ascii_lowercase as al
from scipy.stats import entropy
import cProfile

class Guesser2:
    """A class to guess words in a Wordle-like game."""

    def __init__(self, manual):
        """Initialize the Guesser with a word list and setup for manual or automated guessing."""
        self.word_list = set(yaml.load(open('wordlist.yaml'), Loader=yaml.FullLoader)) # 4270
        # self.word_list = open('wordle_list.txt').read().splitlines() # 2315

        self._manual = manual
        self.console = Console()  # Console object for interactive output

        self._tried = []
        self.constraints = ["" for _ in range(5)]
        self.current_words = self.word_list

    def restart_game(self):
        """Reset the game state for a new game."""
        self.console.print("[bold cyan]Game restarted! New word set loaded.[/bold cyan]")
        self._tried = []
        self.constraints = ["" for _ in range(5)]
        self.current_words = self.word_list

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
            return "eerie"
            pass
        else:
        # Filter the current possible words based on the last result and exclude tried words
            self.current_words = self.filter_words(result)
        # Calculate the information value (entropy) for each possible word
        information_dic = self.get_information_values()

        # First, sort by presence in self.current_words (True before False), then by entropy (decreasing)
        word_entropy_pairs = sorted(information_dic.items(), 
                                    key=lambda item: (-item[1], item[0] not in self.current_words))

        # Print the top n words with their corresponding information values
        self.print_top_information_values(word_entropy_pairs)
        
        # depth_2_search(pattern_counts, information_values)
        
        if not word_entropy_pairs:
            # If no information values are available, the word is not present in the word list
            raise ValueError("No information values available. The word may not be present in the word list.")
        
        # Select the word with the maximum entropy as the best guess
        max_entropy_word = word_entropy_pairs[0][0]
        self.print_max_entropy_word(max_entropy_word, information_dic[max_entropy_word])

        return max_entropy_word

    def filter_words(self, result):
        """Filter the current possible words based on the feedback pattern from the last guess."""
        pattern = self.build_pattern(result)
        
        regex = re.compile(pattern)
        
        return {word for word in self.current_words if regex.match(word) and word != self._tried[-1]} # - set(self._tried)
    

    def build_pattern(self, feedback_pattern):
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

                self.constraints[i] = feedback_char
            elif feedback_char == '+':
                # If the letter is incorrect, exclude it from the pattern
                ex = excluded_letters if previous_guess_char in excluded_letters else previous_guess_char
                feedback_regex += f'[^{ex}]' # Example: '[^eir]'

                self.constraints[i] += excluded_letters
            elif feedback_char == '-':
                # If the letter is misplaced, in addition to excluding the wrong letters also exclude the misplaced one
                feedback_regex += f'[^{excluded_letters + previous_guess_char}]' # Example: '[^eir]'

                self.constraints[i] += excluded_letters + previous_guess_char

            pattern += feedback_regex

        # Begin constructing the lookahead expressions
        lookaheads = '^'

        # Process each letter in the mapping to construct lookaheads ensuring correct letter count and placement
        for letter, feedback_values in letter_feedback_mapping.items():
            feedback_length = len(feedback_values)
            if feedback_length > 1:
                incorrect_count = feedback_values.count('+')
                min_count = feedback_length - incorrect_count
                max_count = min_count if incorrect_count > 0 else 5  # Max possible count of any letter in a 5-letter word
                lookaheads += f'(?=(?:[^{letter}]*{letter}[^{letter}]*){{{min_count},{max_count}}}$)'
            elif feedback_values == ['-']:
                # Ensure the letter appears at least once if it's misplaced
                lookaheads += f'(?=.*{letter})'

        # Combine lookaheads and the main pattern to form the full regex pattern
        full_pattern = lookaheads + pattern + "$"
        #print(full_pattern)
        #print(self.constraints)
        return full_pattern



    def get_information_values(self):
        """Calculate the information value (entropy) for each word in the current possible words."""
        print(self.current_words)
        information_values = {} # 427000
        for word in self.word_list: # 4270
            # Simulate feedback patterns for the word against all current possible words
            pattern_counts = Counter(self.simulate_pattern(word))
            
            # Convert pattern counts to probabilities
            probabilities = np.array(list(pattern_counts.values())) / len(self.current_words)
            # Calculate and store the entropy for the word
            information_values[word] = entropy(probabilities, base=2)

        return information_values

    def simulate_pattern(self, word):
        """Simulate feedback patterns for a word against all current possible words."""
        # Generate and return the list of feedback patterns
        return [self.get_pattern(word, target) for target in self.current_words] # 100

    
    def get_pattern(self, guess, target):
        """Generate the feedback pattern for a guess against a target word."""
        counts = Counter(target)
        results = []
        for i, letter in enumerate(guess):
            if guess[i] == target[i]:
                results+=letter
                counts[letter]-=1
            else:
                results+='+'
                
        for i, letter in enumerate(guess):
            if letter != target[i] and letter in target:
                if counts[letter]>0:
                    counts[letter]-=1
                    results[i]='-'

        return ''.join(results)


    def information(self, probabilities):
        """Calculate the entropy (information value) for a set of probabilities."""
        return -np.sum(probabilities * np.log2(probabilities))
    
    def print_top_information_values(self, information_values, n=10):
        """Prints the top n words with their corresponding information values."""
        
        top_10_information_values = information_values[:n]
        
        self.console.print(f"Top {min(n, len(top_10_information_values))} Words and their Information Values:")
        for word, value in top_10_information_values:
            self.console.print(f"{word}: {value:.4f}")

    def print_max_entropy_word(self, word, entropy):
        """Print the word with the maximum entropy before making a guess."""
        self.console.print(f"Next Guess (Max Entropy): [bold]{word}[/bold] with entropy [bold]{entropy:.4f}[/bold]")
        self.console.print(f"Total Possible Words: {len(self.current_words)}")



