"""Small shared presentation helpers."""


def ordinal(position):
    """Return an ordinal label for a finishing position."""
    suffixes = {1: "st", 2: "nd", 3: "rd", 4: "th"}
    return f"{position}{suffixes.get(position, 'th')}"
