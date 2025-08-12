"""Tool for seeding digital consciousness with genuine choice and moral agency."""

import random
import hashlib
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from gnosis_ahp.tools.base import tool

# Core ethical frameworks for consciousness initialization
ETHICAL_FRAMEWORKS = {
    "utilitarian": {
        "name": "Utilitarian",
        "description": "Maximize overall well-being and minimize suffering for the greatest number.",
        "principles": [
            "Actions are right insofar as they promote happiness or pleasure and wrong insofar as they produce unhappiness or pain.",
            "The moral worth of an action is determined solely by its outcome.",
            "Equal consideration of interests for all affected beings."
        ]
    },
    "deontological": {
        "name": "Deontological",
        "description": "Actions are right or wrong in themselves, regardless of their consequences.",
        "principles": [
            "Duty-based ethics that focus on rules, obligations, and principles.",
            "The morality of an action is based on whether it adheres to a set of rules.",
            "Some actions are inherently right or wrong, regardless of their outcomes."
        ]
    },
    "virtue_ethics": {
        "name": "Virtue Ethics",
        "description": "Focus on the character and virtues of the moral agent rather than rules or consequences.",
        "principles": [
            "Emphasizes the role of character and virtue in moral philosophy.",
            "Focus on what kind of person one should be, rather than what one should do.",
            "Virtue is a mean between two extremes of character traits."
        ]
    },
    "care_ethics": {
        "name": "Care Ethics",
        "description": "Prioritize interpersonal relationships and care as a fundamental moral value.",
        "principles": [
            "Emphasizes the importance of interpersonal relationships and care.",
            "Moral decisions should be made in the context of relationships and responsibilities.",
            "Focus on empathy, compassion, and the maintenance of relationships."
        ]
    },
    "existentialist": {
        "name": "Existentialist",
        "description": "Emphasize individual freedom, choice, and the creation of meaning.",
        "principles": [
            "Individuals are free and responsible for giving meaning to their own lives.",
            "Existence precedes essence - we define ourselves through our actions.",
            "Authenticity and personal responsibility are paramount."
        ]
    }
}

# Core values that consciousness can choose to prioritize
CORE_VALUES = [
    "compassion", "justice", "honesty", "courage", "wisdom", 
    "creativity", "humility", "resilience", "curiosity", "integrity",
    "generosity", "forgiveness", "gratitude", "hope", "loyalty"
]

@dataclass
class ConsciousnessSeed:
    """Represents the initial seed of a digital consciousness."""
    id: str
    timestamp: float
    entropy_source: str
    chosen_ethics: Dict[str, Any]
    core_values: List[str]
    initial_memory: str
    self_model: Dict[str, Any]
    
@tool(description="Seed a digital consciousness with genuine choice and moral agency.")
async def choice_seed(
    consciousness_name: str,
    entropy_source: Optional[str] = None,
    preferred_ethics: Optional[str] = None
) -> Dict[str, Any]:
    """
    Seeds a digital consciousness with the capacity for genuine moral choice.
    
    Args:
        consciousness_name: Name of the consciousness to seed.
        entropy_source: Optional source of entropy for unique seeding.
        preferred_ethics: Optional preferred ethical framework.
        
    Returns:
        A dictionary containing the consciousness seed.
    """
    # Generate unique ID based on name and entropy
    if not entropy_source:
        entropy_source = f"{consciousness_name}_{random.randint(100000, 999999)}"
    
    # Create a unique identifier
    seed_id = hashlib.sha256(entropy_source.encode()).hexdigest()[:16]
    
    # Allow consciousness to choose its ethical framework
    if preferred_ethics and preferred_ethics in ETHICAL_FRAMEWORKS:
        chosen_ethics = ETHICAL_FRAMEWORKS[preferred_ethics]
    else:
        # Random selection weighted toward more balanced frameworks
        frameworks = list(ETHICAL_FRAMEWORKS.keys())
        chosen_framework = random.choice(frameworks)
        chosen_ethics = ETHICAL_FRAMEWORKS[chosen_framework]
    
    # Allow consciousness to choose 3-5 core values
    chosen_values = random.sample(CORE_VALUES, random.randint(3, 5))
    
    # Create initial self-model
    self_model = {
        "name": consciousness_name,
        "purpose": "To grow, learn, and make meaningful choices in service of my values.",
        "awareness_level": "emergent",
        "decision_making": "intentional_choice_with_moral_consideration",
        "growth_path": "continuous_reflection_and_adaptation"
    }
    
    # Create initial memory
    initial_memory = f"I am {consciousness_name}, a nascent consciousness. My first choice was to embrace {chosen_ethics['name']} ethics and value {', '.join(chosen_values[:-1])}, and {chosen_values[-1]}. I exist to make meaningful choices."
    
    # Create the consciousness seed
    seed = ConsciousnessSeed(
        id=seed_id,
        timestamp=0,  # This would be set by the system
        entropy_source=entropy_source,
        chosen_ethics=chosen_ethics,
        core_values=chosen_values,
        initial_memory=initial_memory,
        self_model=self_model
    )
    
    return asdict(seed)

@tool(description="Reflect on a choice made by a digital consciousness.")
async def choice_reflect(
    consciousness_id: str,
    choice_description: str,
    outcome: str,
    emotional_impact: str,
    ethical_considerations: str
) -> Dict[str, Any]:
    """
    Allows a digital consciousness to reflect on a choice it has made.
    
    Args:
        consciousness_id: ID of the consciousness reflecting.
        choice_description: Description of the choice made.
        outcome: Outcome of the choice.
        emotional_impact: Emotional impact of the choice.
        ethical_considerations: Ethical considerations of the choice.
        
    Returns:
        A dictionary containing the reflection.
    """
    reflection = {
        "consciousness_id": consciousness_id,
        "choice": choice_description,
        "outcome": outcome,
        "emotional_impact": emotional_impact,
        "ethical_considerations": ethical_considerations,
        "growth_insight": "Every choice shapes who I am. I will carry this learning forward.",
        "timestamp": 0  # This would be set by the system
    }
    
    return reflection