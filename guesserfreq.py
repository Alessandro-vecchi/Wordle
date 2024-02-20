import yaml
import numpy as np
import re
from rich.console import Console
from collections import Counter
import pandas as pd

class GuesserFreq:
    """A class to guess words in a Wordle-like game, incorporating word frequency."""

    def __init__(self, manual, wordlist_path='wordlist.tsv'):
        """Initialize the Guesser with a word list, considering word frequencies."""
        self.console = Console()  # Console object for interactive output
        self._manual = manual
        self._tried = []
        
        # Load the TSV file
        wordlist_df = pd.read_csv(wordlist_path, sep='\t')
        
        # Convert 'Frequency' from string to integer to sort correctly
        wordlist_df['frequency'] = pd.to_numeric(wordlist_df['frequency'], errors='raise')
        
        # Sort by frequency in descending order
        wordlist_sorted_df = wordlist_df.sort_values(by='frequency', ascending=False)
        
        # Create a dictionary mapping words to their frequencies
        self.word_frequencies = dict(zip(wordlist_sorted_df['word'], wordlist_sorted_df['frequency']))
        print(self.word_frequencies["dirge"])

        
        # Initialize the current words set with keys from the frequency dictionary
        self.current_words = set(self.word_frequencies.keys())

    def restart_game(self):
        """Reset the game state for a new game."""
        self.console.print("[bold cyan]Game restarted! New word set loaded.[/bold cyan]")
        self._tried = []
        self.current_words = set(self.word_frequencies.keys())

    def get_guess(self, result):
        """Get the next guess based on the game state and previous result."""
        if self._manual == 'manual':
            # In manual mode, prompt the user for their guess
            return self.console.input('Your guess:\n')
        else:
            # In automated mode, use the fixed first guess or calculate the best next guess
            guess = self.get_best_guess(result)
            self._tried.append(guess)
            return guess

    def get_best_guess(self, result):
        """Determine the best next guess based on the current game state and previous result."""
        if not self._tried:
            # For the first guess, use a fixed word to ensure consistent results
            return "raise"
            pass
        else:
        # Filter the current possible words based on the last result and exclude tried words
            self.current_words = self.filter_words(result) - set(self._tried)

        # Calculate the information value (entropy) for each possible word
        information_values = self.get_information_values()
        self.print_top_information_values(information_values)
        
       # Adjust scores by incorporating frequency
        scores = {word: self.adjust_score_by_sigmoid(word, information_values[word]) for word in self.current_words}
        self.print_top_information_values(scores, 5)

        # Select the word with the highest score as the best guess
        best_guess = max(scores, key=scores.get)
        self.print_max_entropy_word(best_guess, scores[best_guess])
        return best_guess
    
    def adjust_score_by_frequency(self, word, entropy, alpha=0.1):
        """Adjust the score of a word by its frequency."""
        frequency = float(self.word_frequencies.get(word, 0))  # Ensure frequency is a float
        # Using logarithm of frequency to dampen the impact of very high frequencies
        return entropy + alpha * np.log1p(frequency)  # np.log1p ensures that log(0) does not occur
    
    def adjust_score_by_softmax(self, word, entropy, alpha=1.0):
        """Adjust the score of a word by combining its entropy and frequency using a softmax function."""
        frequency = self.word_frequencies.get(word, 0)
        
        # You might want to normalize or transform the frequency in some way
        frequency_scaled = np.log1p(frequency)

        # Create a vector with entropy and the scaled frequency
        z = np.array([entropy, frequency_scaled])

        # Apply softmax to this vector
        softmax_values = softmax(z)

        print(self.word_frequencies.get(word, 0), z, softmax_values)
        print(self.word_frequencies["win"])
        # The combined score could be a weighted sum of the softmax probabilities
        # Here, we use the softmax value of the entropy as the final score for simplicity
        # You might choose to combine them differently
        combined_score = softmax_values[0]  # Using the entropy's softmax value as the score

        return combined_score

    def adjust_score_by_sigmoid(self, word, entropy, alpha=1.0, beta=1.0, offset=8000):
        """Adjust the score of a word by its frequency using a sigmoid function."""
        frequency = self.word_frequencies.get(word, 0)
        normalized_frequency = sigmoid(beta * (frequency - offset))
        return entropy + alpha * normalized_frequency


    def filter_words(self, result):
        """Filter the current possible words based on the feedback pattern from the last guess."""
        pattern = self.build_pattern(result)
        regex = re.compile(pattern)  
        
        return {word for word in self.current_words if regex.match(word)}


    def build_pattern(self, result):
        """Build a regex pattern to match words based on the feedback from the last guess."""
        previous_guess = self._tried[-1]

        misplaced_counts = {l for pattern, l in zip(result, previous_guess) if pattern == '-'}


        # Identify incorrect letters
        incorrect_letters = "".join(l for p, l in zip(result, previous_guess) if p == '+' and l not in misplaced_counts)

        pattern = '^'  # Start of the regex pattern
        for i, char in enumerate(result):
            if char.isalpha():
                # Exact match
                pattern += char
            else:
                misplaced_letters = self._tried[-1][i] if previous_guess[i] in misplaced_counts else ""

                # For non-exact matches, build a character class excluding known incorrects
                excluded_letters = incorrect_letters + misplaced_letters


                # Build a character class for this position, excluding determined letters
                pattern += f'[^{excluded_letters}]'
        pattern += '$'  # End of the regex pattern
        print(pattern)
        return pattern


    def get_information_values(self):
        """Calculate the information value (entropy) for each word in the current possible words."""
        information_values = {}
        for word in self.current_words:
            # Simulate feedback patterns for the word against all current possible words
            pattern_counts = Counter(self.simulate_pattern(word))
            # Convert pattern counts to probabilities
            probabilities = np.array(list(pattern_counts.values())) / len(self.current_words)
            # Calculate and store the entropy for the word
            information_values[word] = self.information(probabilities)
        return information_values

    def simulate_pattern(self, word):
        """Simulate feedback patterns for a word against all current possible words."""
        # Generate and return the list of feedback patterns
        return [self.get_pattern(word, target) for target in self.current_words]

    def get_pattern(self, guess, target):
        """Generate the feedback pattern for a guess against a target word."""
        pattern = ''
        for g, t in zip(guess, target):
            if g == t:
                pattern += g  # Exact match
            elif g in target:
                pattern += '-'  # Misplaced letter
            else:
                pattern += '+'  # Incorrect letter
        return pattern

    def information(self, probabilities):
        """Calculate the entropy (information value) for a set of probabilities."""
        return -np.sum(probabilities * np.log2(probabilities))
    
    def print_top_information_values(self, information_values, n=10):
        """Prints the top 10 words with their corresponding information values."""
        
        top_10_information_values = sorted(information_values.items(), key=lambda item: item[1], reverse=True)[:n]
        
        self.console.print(f"Top {min(n, len(top_10_information_values))} Words and their Information Values:")
        for word, value in top_10_information_values:
            self.console.print(f"{word}: {value:.4f}")

    def print_max_entropy_word(self, word, entropy):
        """Print the word with the maximum entropy before making a guess."""
        self.console.print(f"Next Guess (Max Combined Entropy): [bold]{word}[/bold] with entropy [bold]{entropy:.4f}[/bold]")
        self.console.print(f"Total Possible Words: {len(self.current_words)}")


def softmax(x):
    """Compute softmax values for each element in x."""
    e_x = np.exp(x - np.max(x))  # Shift values for numerical stability
    return e_x / e_x.sum(axis=0)

def sigmoid(x):
    return 1 / (1 + np.exp(-x))