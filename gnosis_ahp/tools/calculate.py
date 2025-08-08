"""
AHP Tool for calculating mathematical expressions.
"""
import math
from typing import Dict, Any

from gnosis_ahp.tools.base import tool

@tool(description="Calculates mathematical expressions with math module functions.")
async def calculate(expression: str) -> Dict[str, Any]:
    """
    Calculates mathematical expressions with math module functions.
    
    Args:
        expression: Math expression (e.g., "2 + 3 * 4", "sqrt(16) + pi")
    
    Returns:
        Dictionary with result or error information
    """
    # Safe math functions dictionary
    allowed_names = {
        'sqrt': math.sqrt, 'pi': math.pi, 'e': math.e,
        'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
        'log': math.log, 'log10': math.log10, 'exp': math.exp,
        'pow': math.pow, 'ceil': math.ceil, 'floor': math.floor,
        'factorial': math.factorial, 'abs': abs,
        'round': round, 'max': max, 'min': min
    }

    try:
        expression = expression.replace('^', '**')  # Support ^ for powers
        result = eval(expression, {"__builtins__": None}, allowed_names)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": "Calculation failed", "reason": str(e)}
