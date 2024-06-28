"""
This module introduces entropy to the test Markdown files by adding predefined lines of code.
"""

import pathlib


def add_entropy_to_file(file_path: pathlib.Path, lines_of_code: str) -> None:
    """
    Adds lines of code to the specified file.

    Args:
        file_path (str): Path to the .md file.
        lines_of_code (str): List of lines of code to add.
    """
    with open(file_path, "w") as f:
        f.write(lines_of_code)


# Define the lines of code for each file
high_entropy_code = """
    ## Section One: Numbers and Letters
    In a galaxy far, far away, 83742 starships assembled. The quantum flux at 9.81m/s² was **astounding**!
    - Item 1: @x&8lKj$1#d7
    - Item 2: zP9Q6v^5wT!rC
    - Item 3: 4837-19xy#A!z

    The universe expanded at an unprecedented rate, and the ancient scrolls revealed secrets of the cosmos. Among the stars, coded messages in ancient languages were found. The encryption patterns were baffling, yet intriguing.

    - Item 4: !Xh7^Tg9*R5
    - Item 5: 12abC3&8kZ@
    - Item 6: 7mY!4$9xOp#

    Galactic explorers used quantum computers to decipher the hidden meanings. These algorithms, running at a trillion operations per second, unveiled stunningly complex mathematical structures.

    ## Section Two: Random Sentences
    Lorem ipsum dolor sit amet, 42 nebulas in the cosmic sea. Quisque finibus, $100 billion, at ipsum tristique:
    1. `function(x) { return x * 42; }`
    2. The quick brown fox jumps over 13 lazy dogs.
    3. Supercalifragilisticexpialidocious - a word with magic.

    Astronomers discovered that these sentences were not just random, but held clues to the nature of dark matter. Each phrase, a key to unlocking the universes deepest mysteries.

    - The 12th moon of Andromeda was home to a mysterious library.
    - Ancient tomes spoke of a star that never dims.
    - Encryption keys were hidden in nursery rhymes and folklore.

    ### Subsection: Mixed Content
    The library contained scrolls filled with arcane symbols and runes. Scholars spent lifetimes decoding the cryptic texts. Their findings led to breakthroughs in understanding the fabric of spacetime.

    - *Equation 1*: E = mc² + quantum flux factor.
    - *Historical Note*: The lost civilization of Xanthar used binary stars for navigation.
    - *Trivia*: 53% of the known universe is composed of dark energy.

    The interplay between known sciences and these ancient texts opened new frontiers. Researchers combined classical mechanics with quantum theory, revealing astonishing new realms.

    ### Subsection: Enigmatic Equations
    The equations inscribed in ancient relics often seemed paradoxical, defying known laws of physics. However, they consistently predicted phenomena with uncanny accuracy.

    - Equation: ψ(x, t) = A exp[i(kx - ωt)]
    - Algorithm: Qsort(arr[], low, high)
    - Formula: Σ (i=1 to n) i² = n(n + 1)(2n + 1) / 6

    These mathematical constructs guided spacefarers through wormholes and temporal anomalies. The synthesis of ancient knowledge with modern science propelled humanity to the stars.

    The journey to understand and harness these codes continues, with each discovery bringing new questions and deeper mysteries.
"""


low_entropy_code = """
        ## Simple List
        - Item 1
        - Item 2
        - Item 3
        - Item 4
        - Item 5
    """


def insert_entropy(base_path: pathlib.Path) -> None:
    entropy_levels = {
        base_path / "high_entropy/high_entropy.md": high_entropy_code,
        base_path / "low_entropy/low_entropy.md": low_entropy_code,
    }
    # Add entropy to each file
    for file_path, lines_of_code in entropy_levels.items():
        add_entropy_to_file(file_path, lines_of_code)
