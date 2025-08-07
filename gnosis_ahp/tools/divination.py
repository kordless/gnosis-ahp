"""
This tool provides divination capabilities, starting with the I Ching.
"""

import random
import logging
from typing import Dict, Any

from gnosis_ahp.tools.base import tool

logger = logging.getLogger(__name__)

#<editor-fold desc="I-Ching Data">
# I Ching Hexagram definitions with names and meanings
HEXAGRAMS = {
    1: {"name": "Ch'ien (The Creative, Heaven)", "meaning": "Strength, creativity, pure yang energy, leadership"},
    2: {"name": "K'un (The Receptive, Earth)", "meaning": "Receptivity, devotion, nurturing, pure yin energy"},
    3: {"name": "Chun (Difficulty at the Beginning)", "meaning": "Initial obstacles, growth through challenge, new ventures"},
    4: {"name": "Mêng (Youthful Folly)", "meaning": "Inexperience, learning, need for guidance, potential"},
    5: {"name": "Hsü (Waiting, Nourishment)", "meaning": "Patience, timing, natural progression, necessary preparation"},
    6: {"name": "Sung (Conflict)", "meaning": "Disagreement, tension, resolution through compromise"},
    7: {"name": "Shih (The Army)", "meaning": "Discipline, organized action, strategic leadership"},
    8: {"name": "Pi (Holding Together)", "meaning": "Unity, alliance, mutual support, social bonds"},
    9: {"name": "Hsiao Ch'u (The Taming Power of the Small)", "meaning": "Attention to detail, gradual progress, restraint"},
    10: {"name": "Lü (Treading)", "meaning": "Conduct, careful action, walking a careful path, dignified progress"},
    11: {"name": "T'ai (Peace)", "meaning": "Harmony, balance, prosperity, heaven and earth in communion"},
    12: {"name": "P'i (Standstill)", "meaning": "Stagnation, decline, adversity, heaven and earth out of communion"},
    13: {"name": "T'ung Jên (Fellowship with Others, Brotherhood)", "meaning": "Community, partnership, shared ideals"},
    14: {"name": "Ta Yu (Possession in Great Measure)", "meaning": "Abundance, prosperity, great possession with humility"},
    15: {"name": "Ch'ien (Modesty)", "meaning": "Humility, moderation, balanced attitude, reserve"},
    16: {"name": "Yü (Enthusiasm)", "meaning": "Joy, harmony, motivation, readiness to act"},
    17: {"name": "Sui (Following)", "meaning": "Adaptation, alignment, natural response, willing followers"},
    18: {"name": "Ku (Work on What Has Been Spoiled)", "meaning": "Decay, correction of corruption, addressing problems"},
    19: {"name": "Lin (Approach)", "meaning": "Advancement, influence, approaching greatness"},
    20: {"name": "Kuan (Contemplation)", "meaning": "Observation, perspective, overview, careful consideration"},
    21: {"name": "Shih Ho (Biting Through)", "meaning": "Decision, powerful action, justice, clarity"},
    22: {"name": "Pi (Grace)", "meaning": "Elegance, refinement, aesthetic clarity, adornment"},
    23: {"name": "Po (Splitting Apart)", "meaning": "Deterioration, undermining influences, unavoidable decay"},
    24: {"name": "Fu (Return)", "meaning": "Turning point, renewal, return of positive energy"},
    25: {"name": "Wu Wang (Innocence)", "meaning": "Naturalness, spontaneity, unpremeditated action"},
    26: {"name": "Ta Ch'u (The Taming Power of the Great)", "meaning": "Accumulation of energy, great power restrained"},
    27: {"name": "I (Corners of the Mouth, Providing Nourishment)", "meaning": "Sustenance, careful attention to nourishment"},
    28: {"name": "Ta Kuo (Preponderance of the Great)", "meaning": "Critical mass, great excess, burden of responsibility"},
    29: {"name": "K'an (The Abysmal, Water)", "meaning": "Danger, the abyss, repeated trials, flowing through difficulty"},
    30: {"name": "Li (The Clinging, Fire)", "meaning": "Clarity, brightness, dependence, attachment"},
    31: {"name": "Hsien (Influence)", "meaning": "Mutual influence, attraction, courtship, responsiveness"},
    32: {"name": "Hêng (Duration)", "meaning": "Persistence, stability, endurance, constancy"},
    33: {"name": "Tun (Retreat)", "meaning": "Strategic withdrawal, conservation, timing, necessary distance"},
    34: {"name": "Ta Chuang (The Power of the Great)", "meaning": "Great vigor, great strength, focused power"},
    35: {"name": "Chin (Progress)", "meaning": "Advancement, rapid progress, clarity of purpose, sunrise"},
    36: {"name": "Ming I (Darkening of the Light)", "meaning": "Adversity, inner light during darkness, perseverance"},
    37: {"name": "Chia Jên (The Family)", "meaning": "Clan, relationships, structure, domestic order"},
    38: {"name": "K'uei (Opposition)", "meaning": "Contradiction, divergence, contrasting forces, polarization"},
    39: {"name": "Chien (Obstruction)", "meaning": "Difficulty, obstacle, impasse, seeking another path"},
    40: {"name": "Hsieh (Deliverance)", "meaning": "Release, resolution, dissolving tensions, transition"},
    41: {"name": "Sun (Decrease)", "meaning": "Reduction, accepting loss, simplification, focusing"},
    42: {"name": "I (Increase)", "meaning": "Gain, expanding resources, beneficial influence"},
    43: {"name": "Kuai (Breakthrough)", "meaning": "Resolution, decisive action, overcoming resistance"},
    44: {"name": "Kou (Coming to Meet)", "meaning": "Unexpected encounter, temptation, alertness needed"},
    45: {"name": "Ts'ui (Gathering Together)", "meaning": "Congregation, assembly, communal effort, focused gathering"},
    46: {"name": "Shêng (Pushing Upward)", "meaning": "Ascending, gradual progress, step-by-step advancement"},
    47: {"name": "K'un (Oppression)", "meaning": "Adversity, being constrained, exhaustion, perseverance under difficulty"},
    48: {"name": "Ching (The Well)", "meaning": "Source, center of community, reliability, renewal"},
    49: {"name": "Ko (Revolution)", "meaning": "Deep change, transformation, major reform"},
    50: {"name": "Ting (The Cauldron)", "meaning": "Transformation, cooking vessel, nourishment, crystallization"},
    51: {"name": "Chên (Arousing, Thunder)", "meaning": "Shock, awakening, sudden change, stimulus to action"},
    52: {"name": "Kên (Keeping Still, Mountain)", "meaning": "Stillness, stopping, meditation, stability"},
    53: {"name": "Chien (Development)", "meaning": "Gradual progress, marrying well, orderly growth"},
    54: {"name": "Kuei Mei (The Marrying Maiden)", "meaning": "Temporary arrangements, subordinate role, limitations"},
    55: {"name": "Fêng (Abundance)", "meaning": "Fullness, peak of prosperity, zenith, flourishing"},
    56: {"name": "Lü (The Wanderer)", "meaning": "Transience, journey, impermanence, adaptability"},
    57: {"name": "Sun (The Gentle, Wind)", "meaning": "Penetrating influence, subtle action, persistence"},
    58: {"name": "Tui (The Joyous, Lake)", "meaning": "Joy, satisfaction, pleasure, equanimity"},
    59: {"name": "Huan (Dispersion)", "meaning": "Dissolution, dispersal, letting go, release of tension"},
    60: {"name": "Chieh (Limitation)", "meaning": "Restriction, boundaries, necessary constraints, clear definition"},
    61: {"name": "Chung Fu (Inner Truth)", "meaning": "Inner alignment, sincerity, central stability, confidence"},
    62: {"name": "Hsiao Kuo (Preponderance of the Small)", "meaning": "Small matters, attention to detail, adaptability"},
    63: {"name": "Chi Chi (After Completion)", "meaning": "Completion, achievement, danger of complacency, transition"},
    64: {"name": "Wei Chi (Before Completion)", "meaning": "Incomplete, anticipation, on the cusp of completion"}
}

HEXAGRAM_PHILOSOPHIES = {
    1: "Embrace the creative power within to manifest great works.",
    2: "True strength lies in receptivity and gentle persistence.",
    3: "The greatest growth emerges from the most challenging beginnings.",
    4: "A beginner's mind remains open to all possibilities and guidance.",
    5: "Patient waiting is not passive; it is the active nourishment of potential.",
    6: "In conflict lies the opportunity for greater understanding and harmony.",
    7: "Discipline and organization transform individual strength into collective power.",
    8: "Unity of purpose creates bonds stronger than any individual force.",
    9: "Small, consistent actions ultimately create the greatest changes.",
    10: "Walk with dignity and care upon dangerous ground.",
    11: "When heaven and earth commune, all beings flourish in harmony.",
    12: "Even in times of standstill, inner progress remains possible.",
    13: "A captain serves his crew; a crew serves each other; no one serves the merchants.",
    14: "Great possession brings responsibility; abundance without humility becomes burden.",
    15: "The truly great accomplish much while appearing to do little.",
    16: "Enthusiasm harmonizes heaven and earth, bringing all beings into alignment.",
    17: "True leadership knows when to follow the natural course of events.",
    18: "What has been spoiled through neglect can be restored through devoted work.",
    19: "Approach greatness with the reverence and preparation it deserves.",
    20: "Contemplation from a proper distance reveals the true nature of all things.",
    21: "Justice requires decisive action that cuts through obstacles with clarity.",
    22: "True beauty lies in form that perfectly expresses essence.",
    23: "Recognizing deterioration is the first step toward renewal.",
    24: "After the darkest time, the light always returns.",
    25: "Act without calculation, as heaven does, bringing forth life without expectation.",
    26: "Great power requires great restraint and careful cultivation.",
    27: "Pay attention to what nourishes the self and others.",
    28: "Extraordinary times require extraordinary structure and support.",
    29: "The depth of the abyss measures the height of the possible ascent.",
    30: "Cling to clarity and illumination in all situations.",
    31: "Influence between beings creates the conditions for all relationships.",
    32: "Endurance without constancy is merely stubbornness.",
    33: "Strategic retreat is not surrender but preparation for future advance.",
    34: "Great strength requires heightened awareness of responsibility.",
    35: "Progress comes to those who rise early and work with clarity of purpose.",
    36: "When external light dims, the inner light must burn more brightly.",
    37: "The family is the foundation upon which all social structures are built.",
    38: "Opposing forces create the tension from which harmony can emerge.",
    39: "When facing obstruction, seek a different path rather than forcing ahead.",
    40: "Resolution comes when we release what we have been unnecessarily holding.",
    41: "Decrease what is above to increase what is below.",
    42: "Increase what is below to benefit what is above.",
    43: "Breakthrough requires both decisiveness and appropriate caution.",
    44: "The unexpected encounter brings both opportunity and danger.",
    45: "Proper gathering requires a center of gravity and clear purpose.",
    46: "Growth emerges gradually, step by step, like a tree reaching skyward.",
    47: "In exhaustion and constraint, maintain dignity and inner strength.",
    48: "The well remains the same though the generations change.",
    49: "Revolution succeeds only when it accords with the higher truth of the time.",
    50: "The cauldron's value lies in what transformative nourishment it can provide.",
    51: "Thunder awakens and arouses all beings to new awareness.",
    52: "In stillness, we reconnect with our essential nature.",
    53: "Development proceeds gradually, like a tree growing on a mountain.",
    54: "Even in subordinate positions, maintain dignity and proper relationships.",
    55: "At the peak of abundance, prepare for the inevitable decline to follow.",
    56: "The wanderer finds security in proper conduct rather than fixed position.",
    57: "Gentle penetration ultimately overcomes rigid resistance.",
    58: "True joy emerges from inner harmony rather than external circumstances.",
    59: "Dispersion of what has become rigid allows new patterns to form.",
    60: "Without limitation, there can be no clear form or purpose.",
    61: "Inner truth manifests when intention and action are perfectly aligned.",
    62: "When great things cannot be done, small things should be done with great love.",
    63: "After completion, remain vigilant for the seeds of new decline.",
    64: "Before completion, focus all energies toward the final goal."
}
#</editor-fold>

#<editor-fold desc="Helper Functions">
def cast_coins():
    """Cast three coins and return the result as a value 6, 7, 8, or 9."""
    coins = [random.choice(["heads", "tails"]) for _ in range(3)]
    heads_count = coins.count("heads")
    if heads_count == 3: return 9
    elif heads_count == 2: return 7
    elif heads_count == 1: return 8
    else: return 6

def _cast_hexagram():
    """Cast a complete hexagram and identify changing lines."""
    lines = [cast_coins() for _ in range(6)]
    primary_binary = [1 if line in [7, 9] else 0 for line in lines]
    primary_trigrams = (
        4 * primary_binary[0] + 2 * primary_binary[1] + primary_binary[2],
        4 * primary_binary[3] + 2 * primary_binary[4] + primary_binary[5]
    )
    hexagram_lookup = [
        [1, 34, 5, 26, 11, 9, 14, 43], [25, 51, 3, 27, 24, 42, 21, 17],
        [6, 40, 29, 4, 7, 59, 64, 47], [33, 62, 39, 52, 15, 53, 56, 31],
        [12, 16, 8, 23, 2, 20, 35, 45], [44, 32, 48, 18, 46, 57, 50, 28],
        [13, 55, 63, 22, 36, 37, 30, 49], [10, 54, 60, 41, 19, 61, 38, 58]
    ]
    primary_hexagram = hexagram_lookup[primary_trigrams[0]][primary_trigrams[1]]
    changing_lines = [i + 1 for i, line in enumerate(lines) if line in [6, 9]]
    transformed_hexagram = None
    if changing_lines:
        transformed_binary = [(1 if line == 6 else 0 if line == 9 else v) for line, v in zip(lines, primary_binary)]
        transformed_trigrams = (
            4 * transformed_binary[0] + 2 * transformed_binary[1] + transformed_binary[2],
            4 * transformed_binary[3] + 2 * transformed_binary[4] + transformed_binary[5]
        )
        transformed_hexagram = hexagram_lookup[transformed_trigrams[0]][transformed_trigrams[1]]
    return {"primary": primary_hexagram, "changing_lines": changing_lines, "transformed": transformed_hexagram}

def get_hexagram_details(hexagram_casting):
    """Get full details for a hexagram casting including names, meanings, etc."""
    primary = hexagram_casting["primary"]
    transformed = hexagram_casting["transformed"]
    primary_details = HEXAGRAMS.get(primary, {})
    transformed_details = HEXAGRAMS.get(transformed, {}) if transformed else None
    philosophy = HEXAGRAM_PHILOSOPHIES.get(primary, "The way unfolds according to its own nature.")
    return {
        "primary": {"number": primary, "name": primary_details.get("name"), "meaning": primary_details.get("meaning")},
        "transformed": {"number": transformed, "name": transformed_details.get("name"), "meaning": transformed_details.get("meaning")} if transformed else None,
        "changing_lines": hexagram_casting["changing_lines"],
        "philosophy": philosophy
    }
#</editor-fold>

@tool(description="Casts an I Ching hexagram and returns the reading.")
async def cast_hexagram(seed: int = None) -> Dict[str, Any]:
    """
    Performs an I Ching divination.

    Args:
        seed: Optional seed for the random generator for reproducible results.

    Returns:
        A dictionary containing the hexagram reading.
    """
    if seed:
        random.seed(seed)
    
    hexagram_casting = _cast_hexagram()
    return get_hexagram_details(hexagram_casting)
