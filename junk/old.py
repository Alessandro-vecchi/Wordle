from random import choice
import yaml, numpy as np, re
from rich.console import Console


class Guesser:
    '''
        INSTRUCTIONS: This function should return your next guess. 
        Currently it picks a random word from wordlist and returns that.
        You will need to parse the output from Wordle:
        - If your guess contains that character in a different position, Wordle will return a '-' in that position.
        - If your guess does not contain that character at all, Wordle will return a '+' in that position.
        - If you guess the character placement correctly, Wordle will return the character. 

        You CANNOT just get the word from the Wordle class, obviously :)
    '''
    def __init__(self, manual):
        self.word_list = yaml.load(open('wordlist.yaml'), Loader=yaml.FullLoader) # list of 4270 words
        self._manual = manual
        self.console = Console()
        self.outcomes = generate_outcomes()
        self._tried = []

        self.current_words = self.word_list

    def restart_game(self):
        self._tried = []
        self.current_words = self.word_list


    def get_guess(self, result, isFirst = False):
        '''
        This function must return your guess as a string. 
        '''
        if self._manual=='manual':
            return self.console.input('Your guess:\n')
        else:
            if isFirst:
                guess = "crate"
            else:
                guess = self.get_best_guess(result)

            self._tried.append(guess)
            self.console.print(guess)
            
            return guess
        
    def get_best_guess(self, result):
        '''
        This function must return your guess as a string. 
        '''
        # get narrowed list of words that match the result pattern and have not been tried
        self.current_words = list(set(self.filter_words(result, self.word_list)) - set(self._tried))

        # get the information value of each word
        information_values = self.get_information_values()
        #print(sorted(information_values.items(), key=lambda x: x[1])[:10])
        print(information_values[:10])
                
        # Find the word with the maximum entropy
        max_entropy_word = max(information_values, key=information_values.get)
        print(information_values[max_entropy_word])
        
        return max_entropy_word

    
    def get_information_values(self):
        '''
        This function must return the information value of each word.
        '''
        information_values = {}
        for word in self.current_words:
            probabilities = np.array([])
            for pattern in self.outcomes:
                w = self.filter_words(pattern, self.current_words)

                p = self.probability(w)
                probabilities = np.append(probabilities, p)
            
            
            information_values[word] = self.information(probabilities)
        return information_values

    def filter_words(self, result, words):
        
        # get all possible words that match the result
        filtered_words = []

        exact_matches, misplaced_letters, incorrect_letters = self.get_letters(result)

        # Build the regex pattern
        pattern = '^'
        for i, char in enumerate(exact_matches):
            if char.isalpha():  # Exact match
                pattern += '[a-z]' if char == 'L' else char # 'L' stands for any specific letter that is correct.

            else:  # Not an exact match, could be a misplaced letter or any other letter
                # Exclude incorrect letters and ensure misplaced letters are not in their wrong positions
                misp = []
                if result[i] == '-':
                    misp.append(self._tried[-1][i])
                excluded_letters = ''.join(incorrect_letters + misp)
                pattern += f'[^{excluded_letters}]'

        pattern += '$'

        # Filter the word list using the regex pattern
        regex = re.compile(pattern)
        for word in words:
            # Check if the word matches the pattern and contains all the misplaced letters
            if regex.match(word) and all(letter in word for letter in misplaced_letters):
                filtered_words.append(word)

        return filtered_words
    

    def get_letters(self, result):
        exact_matches = [l if l not in ('-', '+') else '.' for l in result]
        
        misplaced_letters = [self._tried[-1][i] for i, l in enumerate(result) if l == '-']

        incorrect_letters = [self._tried[-1][i] for i, l in enumerate(result) if l == '+']

        return exact_matches, misplaced_letters, incorrect_letters
    

    def probability(self, w):
        '''
        This function must return the probability of a particular word given the pattern.
        '''
        return len(w) / len(self.word_list)


    def information(self, p):
        '''
        This function must return the expected information value of the particular guess. 
        '''
        # Filter out zero probabilities to avoid log(0)
        p_nonzero = p[p > 0]

        # Compute the entropy
        entropy = -np.sum(p_nonzero * np.log2(p_nonzero))

        return entropy
    

    def build_pattern_1(self, result):
        """Build a regex pattern to match words based on the feedback from the last guess."""
        previous_guess = self._tried[-1]

        misplaced_counts = [l for pattern, l in zip(result, previous_guess) if pattern == '-']

        # Identify incorrect letters
        incorrect_letters = "".join(l for p, l in zip(result, previous_guess) if p == '+' and l not in misplaced_counts)

        pattern = '^'  # Start of the regex pattern

        # If there are letters that must be included, add a positive lookahead for them
        for l in misplaced_counts:
            pattern += f'(?=.*{l})'

        for i, char in enumerate(result):
            if char.isalpha():
                # Exact match
                pattern += char
            else:
                misplaced_letters = previous_guess[i] if previous_guess[i] in misplaced_counts else ""

                # For non-exact matches, build a character class excluding known incorrects
                excluded_letters = incorrect_letters + misplaced_letters

                # Build a character class for this position, excluding determined letters
                pattern += f'[^{excluded_letters}]'

        pattern += '$'  # End of the regex pattern
        print(pattern)
        return pattern
    
    def build_pattern_2(self, feedback_pattern):
        """Simplified method to construct a regex pattern based on feedback, 
        ensuring correct handling of correct, misplaced, and incorrect letters."""
        
        previous_guess = self._tried[-1]  # The last guess made

        # Initialize pattern components
        lookaheads, pattern_main = '^', ''

        # Trackers for letters based on feedback
        correct_letters = {}
        misplaced_letters = {}
        incorrect_letters = set()

        # Analyze feedback to populate trackers
        for i, (guess_letter, feedback) in enumerate(zip(previous_guess, feedback_pattern)):
            if feedback.isalpha():  # Correct letter
                correct_letters[i] = guess_letter
                pattern_main += guess_letter
            elif feedback == '-':  # Misplaced letter
                misplaced_letters.setdefault(guess_letter, []).append(i)
                pattern_main += '.'
            else:  # Incorrect letter
                incorrect_letters.add(guess_letter)
                pattern_main += '.'
                # pattern_main += f'[^{"".join(incorrect_letters)}]'

        # Construct lookaheads for misplaced letters ensuring their inclusion elsewhere
        for letter, indices in misplaced_letters.items():
            if letter not in incorrect_letters:  # Only add lookaheads for letters not marked as incorrect
                count = len(indices) + sum(1 for i in correct_letters if correct_letters[i] == letter)
                lookahead = f'(?=(?:[^{letter}]*{letter}){{{count},}})'
                if lookahead not in lookaheads:  # Avoid duplicate lookaheads
                    lookaheads += lookahead

        # Handle edge cases for letters that are correct in one place but incorrect or misplaced in another
        for i, letter in correct_letters.items():
            if letter in misplaced_letters or letter in incorrect_letters:
                pattern_main = pattern_main[:i] + f'[^{"".join(incorrect_letters)}{"".join(misplaced_letters.get(letter, []))}]' + pattern_main[i+1:]

        # Combine lookaheads with the main pattern
        full_pattern = lookaheads + pattern_main + '$'
        print(full_pattern)
        return full_pattern

    


def generate_outcomes(level=0, current_pattern=''):
    outcomes = []
    states = ['+', '-', 'L']  # 'L' stands for any specific letter that is correct.

    if level == 5:  # Base case: the pattern is complete
        return [current_pattern]

    for state in states:
        # Recursively build the next level of patterns
        outcomes += generate_outcomes(level + 1, current_pattern + state)

    return outcomes



        