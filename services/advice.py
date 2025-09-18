\
from typing import Dict

# Quick knowledge capsules (augment with your RAG docs for evidence-backed answers).

INJURY_TIPS = {
    "shoulder": [
        "Reduce overhead volume temporarily; emphasize technique and high-elbow catch.",
        "Add rotator cuff work: 3x12 external rotations, scapular retractions.",
        "Mobility: thoracic extension drills; avoid painful ranges."
    ],
    "knee": [
        "Limit intense breaststroke kicks; substitute with dolphin/flutter kick sets.",
        "Quad/hamstring balance work: step-ups, hamstring bridges."
    ],
    "lower_back": [
        "Neutral spine on turns; add core stability (dead bugs, bird dogs).",
        "Hip flexor mobility and glute activation."
    ]
}

NUTRITION_PLANS = {
    "veg": [
        "Pre‑session (60–90m): Oats + banana + nuts; water/electrolyte.",
        "During (>60m hard): 30–45g carb/hr via sports drink or fruit.",
        "Post: Rice + lentils + paneer/tofu; fruit; fluids."
    ],
    "vegan": [
        "Pre: Oats + banana + peanut butter; water/electrolyte.",
        "During: 30–45g carb/hr from dates/raisins/drink.",
        "Post: Rice/quinoa + legumes + veggies; fortified plant yogurt/milk."
    ],
    "non-veg": [
        "Pre: Granola + yogurt + fruit; water/electrolyte.",
        "During: 30–45g carb/hr via drink/gel/fruit.",
        "Post: Rice/pasta + eggs/chicken/fish + veggies; fruit."
    ]
}

def injury_advice(area: str) -> Dict:
    area = area.lower().replace("-", "_").replace(" ", "_")
    tips = INJURY_TIPS.get(area, ["Consult a physio if pain persists; reduce aggravating movements and refine technique."])
    return {"area": area, "tips": tips}

def nutrition_advice(category: str="veg") -> Dict:
    key = category.lower().replace("-", "_")
    plan = NUTRITION_PLANS.get(key, NUTRITION_PLANS["veg"])
    return {"category": key, "plan": plan}
