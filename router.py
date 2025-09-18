\
import re
from typing import Dict
from services.workouts import swim_workout, dryland_workout
from services.analysis import analyze_pace
from services.advice import injury_advice, nutrition_advice
from retrievers import retrieve
from llm_backends import render_prompts, call_llm
import yaml

def load_yaml(path):
    import os, yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def handle_query(q: str, cfg, prompts) -> str:
    ql = q.lower()

    # --- Swim workout
    if any(k in ql for k in ["swim workout", "swim set", "generate swim", "session plan"]):
        # parse crude parameters
        stroke = "free"
        for s in ["free","fly","back","breast","im"]:
            if s in ql:
                stroke = s
                break
        goal = "aerobic"
        for g in ["easy","aerobic","threshold","vo2","sprint"]:
            if g in ql:
                goal = g
                break
        import re
        m = re.search(r"(\d{3,5})\s*m", ql)
        total = int(m.group(1)) if m else 4000
        plan = swim_workout(goal, stroke, total)
        return format_plan(plan)

    # --- Dryland workout
    if any(k in ql for k in ["dryland", "strength", "core", "mobility workout"]):
        focus = "strength"
        for f in ["strength","core","mobility"]:
            if f in ql:
                focus = f
                break
        return format_plan(dryland_workout(focus))

    # --- Pace/Workout analysis
    if "analyze" in ql or "analysis" in ql or "pace" in ql:
        # Expect pattern like: laps=[85,86,86,87]; rest=[20,20,25]; hr=[160,165,168]
        laps = parse_list(q, "laps")
        rest = parse_list(q, "rest")
        hr   = parse_list(q, "hr")
        rep = analyze_pace(laps, rest, hr)
        return pretty_dict(rep)

    # --- Injury advice
    if "injury" in ql or "pain" in ql:
        for area in ["shoulder","knee","lower back","back"]:
            if area in ql:
                return pretty_dict(injury_advice(area))
        return pretty_dict(injury_advice("shoulder"))

    # --- Nutrition
    if "nutrition" in ql or "diet" in ql or "meal" in ql:
        for cat in ["veg","vegan","non-veg","non veg","nonveg"]:
            if cat in ql:
                return pretty_dict(nutrition_advice(cat.replace(" ","-")))
        return pretty_dict(nutrition_advice("veg"))

    # --- Default: RAG answer with local LLM (or context dump)
    snippets = retrieve(q, cfg)
    context = format_context(snippets)
    msgs = render_prompts(q, context, prompts)
    backend = cfg.get("llm_backend", "none")
    model = cfg.get("gpt4all_model") if backend=="gpt4all" else cfg.get("ollama_model")
    return call_llm(backend, model, msgs)

def parse_list(q: str, key: str):
    m = re.search(fr"{key}\s*=\s*\[([^\]]+)\]", q.lower())
    if not m:
        return []
    raw = m.group(1)
    vals = []
    for tok in raw.split(","):
        tok = tok.strip()
        try:
            if "." in tok:
                vals.append(float(tok))
            else:
                vals.append(int(tok))
        except Exception:
            pass
    return vals

def format_plan(plan: Dict) -> str:
    if plan["type"] == "swim":
        lines = [f"SWIM ({plan['total_m']}m) — goal: {plan['goal']} — stroke: {plan['stroke']}",
                 "\nWarm‑up:"]
        lines += [f"- {x}" for x in plan["warmup"]]
        lines += ["\nMain Set:"]
        lines += [f"- {x}" for x in plan["main"]]
        lines += ["\nCool‑down:"]
        lines += [f"- {x}" for x in plan["cooldown"]]
        return "\n".join(lines)
    else:
        lines = [f"DRYLAND — focus: {plan['focus']} — {plan['duration_min']} min", "\nBlocks:"]
        lines += [f"- {x}" for x in plan["blocks"]]
        return "\n".join(lines)

def format_context(snippets, max_chars=2400):
    out = []
    total = 0
    for s in snippets:
        head = f"[{os.path.basename(s['path'])}:{s['span'][0]}-{s['span'][1]}]\n"
        block = head + s["text"].strip()
        if total + len(block) > max_chars:
            break
        out.append(block)
        total += len(block)
    return "\n\n---\n\n".join(out)

def pretty_dict(d: Dict) -> str:
    import json
    return json.dumps(d, indent=2)
