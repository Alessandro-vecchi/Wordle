import re
from string import ascii_lowercase

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
