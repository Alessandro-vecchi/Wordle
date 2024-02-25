import re, numpy as np

""" 
def possible_letters(patterns, word_length):
    # Initialize a list of sets, one for each position in the word
    position_sets = [set(ascii_lowercase) for _ in range(word_length)]

    for pattern in patterns:
        for i in range(word_length):
            # Create a regex pattern to extract the allowed characters for the current position
            pos_pattern = f'^{"." * i}([^{ascii_lowercase}]){"." * (word_length - i - 1)}$'
            match = re.match(pos_pattern, pattern)
            print(pattern, pos_pattern, match)
            if match:
                # If there's a match, remove the characters found from the set for this position
                excluded_chars = match.group(1)
                position_sets[i] -= set(excluded_chars)
            else:
                # If no match, check for explicit inclusions (like 'i' in position 3)
                pos_pattern = f'^{"." * i}([a-z]){"." * (word_length - i - 1)}$'
                match = re.match(pos_pattern, pattern)
                if match:
                    included_char = match.group(1)
                    # Keep only the included character in the set for this position
                    position_sets[i] = {included_char}

    return position_sets

# Example usage with your provided patterns
patterns = [
    '^[^rsa][^rsa]i[^rsa]e$',
    '^(?=.*c)[^lnc][^ln]i[^ln]e$',
    '^[^ju][^ju]ice$'
]

# Assuming a 5-letter word based on your patterns
sets_per_position = possible_letters(patterns, 5)

for i, letter_set in enumerate(sets_per_position):
    print(f"Position {i+1}: {letter_set}")

else:
    target_words = self.guessable_words(result)
    
    info = {}
    for guess in target_words:
        
        patterns = Counter(self.get_matches(guess, target) for target in target_words)
        
        p = np.array(patterns.values()) / len(target_words)
        info[guess] = p * np.log2(p)
        
    entropy = sorted(info.items(), key=info.get, reverse=True)
    # print(entropy[:5])



    guess = entropy[0]

if 1==1:
    pass
else:
    word_subset = self.guessable_words(result)

    for guess in word_subset.keys():
        
        patterns = {self.get_matches(guess,word) for word in word_subset.keys()}
        e = 0
        for pattern in patterns:
            subset = self.guessable_words(pattern)
            p = len(subset)/len(self.word_list)

            e -= p * np.log2(p)
        word_subset[guess] = e
    entropy = sorted(word_subset, key=lambda x: word_subset[x])
    # print(entropy[:5])



    guess = entropy[0] """

C = [[0, 1, 1], [1, 0, 0], [1, 0, 0]]
C = np.array(C)

indices = np.array([1, 1, 0, 1])

#boolean = C[indices] == 1 # [[1 0 0] [1 0 0] [0 1 1] [1 0 0]]
i0, i1 = np.where(C[indices] == 1)
print(i0, i1, indices[i0])
