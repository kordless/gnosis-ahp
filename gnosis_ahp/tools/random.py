"""
AHP Tool for generating various types of random data.
"""
import random
from typing import Dict, Any, Optional

from gnosis_ahp.tools.base import tool

@tool(description="Generate random data, including integers, floats, choices from a list, or cards from a deck.")
async def random_data(
    type: str = "int",
    min: float = 0,
    max: float = 100,
    count: int = 1,
    choices: str = None,
    deck: str = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generates various types of random numbers, selections, or cards.

    Args:
        type: The type of random value. Can be 'int', 'float', 'choice', or 'deck'.
        min: The minimum value for 'int' or 'float' types.
        max: The maximum value for 'int' or 'float' types.
        count: The number of random values to generate.
        choices: A comma-separated list of items to choose from (for 'choice' type).
        deck: The type of card deck to draw from. Currently supports 'standard'.
        seed: An optional seed for the random number generator for reproducible results.

    Returns:
        A dictionary containing the generated random values.
    """
    if seed is not None:
        random.seed(seed)

    if count < 1:
        count = 1
    if count > 1000:
        count = 1000

    result = {
        "type": type,
        "count": count,
        "values": []
    }

    try:
        if type.lower() == "deck":
            if deck.lower() != "standard":
                raise ValueError("Invalid deck type. Currently only 'standard' is supported.")
            
            suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
            ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
            standard_deck = [f"{rank} of {suit}" for suit in suits for rank in ranks]
            
            num_cards = int(count)
            if num_cards > 52:
                num_cards = 52
            
            result["values"] = random.sample(standard_deck, k=num_cards)

        elif type.lower() == "int":
            int_min, int_max = int(min), int(max)
            if int_min > int_max:
                int_min, int_max = int_max, int_min
            result["values"] = [random.randint(int_min, int_max) for _ in range(count)]

        elif type.lower() == "float":
            if min > max:
                min, max = max, min
            result["values"] = [random.uniform(min, max) for _ in range(count)]

        elif type.lower() == "choice":
            if not choices:
                raise ValueError("The 'choices' parameter is required for type 'choice'.")
            items = [item.strip() for item in choices.split(",")]
            num_choices = int(count)
            if num_choices > len(items):
                random.shuffle(items)
                result["values"] = items
            else:
                result["values"] = random.sample(items, k=num_choices)

        else:
            raise ValueError(f"Invalid random type: {type}. Valid types are 'int', 'float', 'choice', 'deck'.")

    except Exception as e:
        return {"success": False, "error": str(e)}

    return {"success": True, "result": result}
