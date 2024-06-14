"""
This script introduces entropy to Markdown files by adding predefined lines of code.

Functions:
- `add_entropy_to_file(file_path, lines_of_code)`: Writes the specified lines to the given file.
- `add_entropy()`: Applies `add_entropy_to_file` to each entry in `entropy_levels`.
"""


def add_entropy_to_file(file_path: str, lines_of_code: str):
    """
    Adds lines of code to the specified file.

    Args:
        file_path (str): Path to the .md file.
        lines_of_code (str): List of lines of code to add.
    """
    with open(file_path, "w") as f:
        for i in lines_of_code:
            f.write(i)


# Define the lines of code for each file
high_entropy_code = """
        ## Section One: Numbers and Letters
        In a galaxy far, far away, 83742 starships assembled. The quantum flux at 9.81m/s² was **astounding**!
        - Item 1: @x&8lKj$1#d7
        - Item 2: zP9Q6v^5wT!rC
        - Item 3: 4837-19xy#A!z
        ## Section Two: Random Sentences
        Lorem ipsum dolor sit amet, 42 nebulas in the cosmic sea. Quisque finibus, $100 billion, at ipsum tristique:
        1. `function(x) { return x * 42; }`
        2. The quick brown fox jumps over 13 lazy dogs.
        3. Supercalifragilisticexpialidocious - a word with magic.
        ### Subsection: Mixed Content
    """

low_entropy_code = """
        ## Simple List
        - Item 1
        - Item 2
        - Item 3
        - Item 4
        - Item 5
    """

# Dictionary of entropy levels for each file
entropy_levels = {
    "high_entropy/high_entropy.md": high_entropy_code,
    "low_entropy/low_entropy.md": low_entropy_code,
}


def add_entropy():
    # Add entropy to each file
    for file_path, lines_of_code in entropy_levels.items():
        add_entropy_to_file(file_path, lines_of_code)