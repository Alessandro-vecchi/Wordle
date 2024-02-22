import numpy as np
import os
import itertools as it
from rich.console import Console

class PatternMatrixGenerator:
    """
    A class to generate and manage a pattern matrix for a Wordle-like game.
    
    Attributes:
        MISS (np.uint8): Constant for letters not in the word.
        MISPLACED (np.uint8): Constant for letters in the word but in the wrong position.
        EXACT (np.uint8): Constant for correct letters in the correct position.
        PATTERN_MATRIX_FILE (str): Filename for saving the generated pattern matrix.
    """
    MISS = np.uint8(0)      
    MISPLACED = np.uint8(1)  
    EXACT = np.uint8(2)     
    
    PATTERN_MATRIX_FILE = "pattern_matrix.npy"

    def __init__(self, word_list):
        """
        Initializes the PatternMatrixGenerator with a given word list.

        Args:
            word_list (list): List of all possible words used in the game.
            grid (np.ndarray): The loaded or generated pattern matrix.
            words_to_index_map (dict): Maps words to their indices in the pattern matrix.
            console (Console): Console object for logging messages.
        """
        self.word_list = word_list

        self.grid = None
        self.words_to_index_map = dict(zip(self.word_list, it.count()))

        self.console = Console()

    @staticmethod
    def words_to_int_arrays(words):
        """
        Converts a list of words to a 2D NumPy array of integer character codes.

        Args:
            words (list): List of words to convert.

        Returns:
            np.ndarray: 2D array of integer character codes of dimension (len(words), 5).
        """
        return np.array([[ord(c) for c in word] for word in words], dtype=np.uint8)

    def generate_pattern_matrix(self):
        """
        Generates the pattern matrix for all pairs of words in the word list.
        
        Returns:
            np.ndarray: The generated pattern matrix.
        """
        guess_words, target_words = self.word_list, self.word_list
        guess_array, target_array = self.words_to_int_arrays(guess_words), self.words_to_int_arrays(target_words) # (n_gw, n_l), (n_tw, n_l)
        n_l = len(guess_words[0])

        # Initialize the feedback pattern matrix with MISS values
        pattern_matrix = np.full((len(guess_words), len(target_words), n_l), self.MISS, dtype=np.uint8)

        # Check for exact matches (EXACT positions)
        for i in range(n_l):
            exact_matches = guess_array[:, i:i+1] == target_array[:, i] # (n_gw, 1); row vector (n_tw, ) seen as a (n_tw, n_tw); the first is broadcaste to (n_gw, n_gw)
            pattern_matrix[:, :, i][exact_matches] = self.EXACT

        # Check for misplaced letters (MISPLACED positions)
        for i, j in it.product(range(n_l), repeat=2):
            if i != j:
                misplaced_matches = (guess_array[:, i:i+1] == target_array[:, j]) & (pattern_matrix[:, :, j] != self.EXACT) & (pattern_matrix[:, :, i] != self.EXACT)
                pattern_matrix[:, :, i][misplaced_matches] = self.MISPLACED

        # Rather than representing a color pattern as a lists of integers,
        # store it as a single integer, whose ternary representations corresponds
        # to that list of integers.
        #print(guess_words[0], pattern_matrix[0][645], target_words[645])
        pattern_matrix = np.dot(pattern_matrix, (3**np.arange(n_l)).astype(np.uint8))
        #print(pattern_matrix[0][645])
        #print(pattern_matrix)
        return pattern_matrix

    def save_pattern_matrix(self, pattern_matrix):
        """
        Saves the given pattern matrix to a file.

        Args:
            pattern_matrix (np.ndarray): The pattern matrix to save.
        """
        np.save(self.PATTERN_MATRIX_FILE, pattern_matrix)

    def load_pattern_matrix(self):
        """
        Loads the pattern matrix from a file, or generates and saves it if not present.
        """
        if not os.path.exists(self.PATTERN_MATRIX_FILE):
        
            self.console.log("\n".join([
                    "Generating pattern matrix. This takes a minute, but",
                    "the result will be saved in a file so that it only",
                    "needs to be computed once.", 
                ]), style="bold yellow")
            
            # Generate the pattern matrix
            pattern_matrix = self.generate_pattern_matrix()

            # Save the generated matrix to a file
            self.save_pattern_matrix(pattern_matrix)

            # Log the completion of the matrix generation
            self.console.log("Pattern matrix generated and saved to file.",
                                style="bold green")

        self.grid = np.load(self.PATTERN_MATRIX_FILE)
    
    def get_pattern_matrix(self, guess_words, target_words):
        """
        Retrieves a submatrix of the pattern matrix for the specified guess and target words.

        Args:
            guess_words (list): List of guess words.
            target_words (list): List of target words.

        Returns:
            np.ndarray: Submatrix of the pattern matrix corresponding to the guess and target words.
        """
        # Load the pattern matrix if it hasn't been loaded already
        if self.grid is None:
            self.load_pattern_matrix()
        
        # Map guess and target words to their indices in the pattern matrix
        indices_guess_words = [self.words_to_index_map[w] for w in guess_words]
        indices_target_words = [self.words_to_index_map[w] for w in target_words]

        # Return the relevant submatrix of the pattern matrix
        # Return pattern entries on the rows of the guess words and columns of the target words
        return self.grid[np.ix_(indices_guess_words, indices_target_words)]