\
from typing import Dict, List

# Simple rule-based generators (no paid dependencies). Customize tables as needed.

STROKE_OPTIONS = ["free", "fly", "back", "breast", "im"]
INTENSITY_ZONES = {
    "easy": (0.6, 0.72),
    "aerobic": (0.72, 0.82),
    "threshold": (0.83, 0.90),
    "vo2": (0.90, 0.96),
    "sprint": (0.96, 1.00),
}

def swim_workout(goal: str = "aerobic", stroke: str = "free", total_m: int = 4000) -> Dict:
    stroke = stroke.lower()
    if stroke not in STROKE_OPTIONS:
        stroke = "free"
    goal = goal.lower()
    if goal not in INTENSITY_ZONES:
        goal = "aerobic"

    warmup = [
        f"400 {stroke} easy",
        f"4x100 {stroke} drills @20\" rest",
        "4x50 kick @15\" rest"
    ]

    if goal in ("aerobic", "easy"):
        main = [
            f"5x{int(total_m*0.12)} {stroke} @ moderate pace (Z2/Z3), 30\" rest",
            f"4x{int(total_m*0.10)} IM as 25 each stroke, smooth, 30\" rest",
            f"8x50 {stroke} build 1-4, 5-8, 20\" rest"
        ]
    elif goal in ("threshold",):
        main = [
            f"3x{int(total_m*0.20)} {stroke} @ threshold (T-pace), 1' rest",
            f"8x50 {stroke} descend 1-4 twice to T-pace, 20\" rest",
        ]
    elif goal in ("vo2", "sprint"):
        main = [
            f"16x50 {stroke} @ VO2 (hard), 30\" rest",
            f"8x25 {stroke} sprint from a push, 30\" rest",
            "4x50 easy choice recovery",
        ]
    else:
        main = [f"{total_m-1000} mixed {stroke}/IM @ moderate, 30\" rest as needed"]

    cooldown = ["200 easy choice", "4x50 choice drills"]
    plan = {"type": "swim", "goal": goal, "stroke": stroke, "total_m": total_m,
            "warmup": warmup, "main": main, "cooldown": cooldown}
    return plan

def dryland_workout(focus: str = "strength", duration_min: int = 45) -> Dict:
    focus = focus.lower()
    blocks: List[str] = []

    if focus == "strength":
        blocks = [
            "3x10 Goblet Squats",
            "3x8 Push-ups (tempo 3-1-1)",
            "3x10 Bent-Over Rows",
            "3x12 Hip Bridges",
            "Core: 3x30s Plank + 3x12 Dead Bugs"
        ]
    elif focus == "core":
        blocks = [
            "4x30s Plank (front/side/side)",
            "3x12 Hollow Body Rocks",
            "3x12 Superman Holds (2s pause)",
            "3x15 Russian Twists"
        ]
    elif focus == "mobility":
        blocks = [
            "10min Dynamic Flow (hips, T-spine, shoulders)",
            "3x10 World’s Greatest Stretch (each side)",
            "3x10 Shoulder CARs + 3x10 Hip CARs",
            "Band work: 3x12 External Rotations"
        ]
    else:
        blocks = [
            "Circuit x3: 12 Air Squats, 8 Push-ups, 12 Lunges, 10 Band Rows, 15s Side Planks"
        ]

    return {"type": "dryland", "focus": focus, "duration_min": duration_min, "blocks": blocks}
