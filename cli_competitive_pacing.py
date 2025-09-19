#!/usr/bin/env python3
"""Standalone Competitive Pacing CLI."""

import re, json
from pathlib import Path

def parse_time(s: str) -> float:
    """Accepts 'ss', 'ss.xxx', 'mm:ss', 'mm:ss.xx', 'mm:ss:cc' (cc=centiseconds), and 'hh:mm:ss[.xx]'."""
    s = str(s).strip().replace(",", ".")
    parts = s.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        elif len(parts) == 2:
            mm, ss = parts
            return float(mm) * 60.0 + float(ss)
        elif len(parts) == 3:
            a, b, c = parts
            if re.fullmatch(r"\d{1,2}", c) and re.fullmatch(r"\d{1,2}", b) and re.fullmatch(r"\d{1,2}", a):
                return float(int(a) * 60 + int(b) + int(c) / 100.0)
            return float(a) * 3600.0 + float(b) * 60.0 + float(c)
        else:
            head, tail = parts[:-1], parts[-1]
            base = 0.0
            for p in head:
                base = base * 60.0 + float(p)
            return base * 60.0 + float(tail)
    except Exception as e:
        raise ValueError(f"Could not parse time string '{s}': {e}")

def format_time(sec: float) -> str:
    if sec is None: return "NA"
    if sec < 60: return f"{sec:.2f}s"
    m = int(sec // 60); s = sec - 60*m
    return f"{m}:{s:05.2f}"

def ideal_fractions(n_splits: int, strategy: str = "even") -> list:
    strategy = (strategy or "even").lower()
    base = [1.0/n_splits]*n_splits; curve = [0.0]*n_splits
    for i in range(n_splits):
        x = i/(n_splits-1) if n_splits>1 else 0.0
        curve[i] = (0.04*(x-0.5))
    if strategy=="negative": curve=[c*1.5 for c in curve]
    elif strategy=="positive": curve=[-c*1.5 for c in curve]
    fracs=[max(1e-6,b+c) for b,c in zip(base,curve)]
    s=sum(fracs); return [f/s for f in fracs]

def project_50_split(pb50: float, distance: int) -> float:
    n = max(1, distance//50); fatigue = 1.0 + 0.03*max(0, n-2)
    return pb50*fatigue

def prerace_flow():
    print("\n=== PRE-RACE SETUP ===")
    stroke = input("Stroke (Freestyle/Backstroke/Breaststroke/Butterfly/IM): ").strip() or "Freestyle"
    distance = int(input("Event distance (m): ").strip())
    pb50 = parse_time(input("Your 50m PB (e.g., 22.28 or 0:22.28): ").strip())
    target_time = parse_time(input("Target FINAL time (e.g., 1:45.00): ").strip())
    strategy = input("Strategy (even/negative/positive) [even]: ").strip().lower() or "even"
    n_splits=max(1,distance//50); fracs=ideal_fractions(n_splits,strategy=strategy)
    ideal=[target_time*f for f in fracs]; cum=[sum(ideal[:i+1]) for i in range(len(ideal))]
    base50=project_50_split(pb50,distance)
    print("\nSuggested 50-splits:")
    for i,s in enumerate(ideal,1):
        delta=s-base50; sign="+" if delta>=0 else ""
        print(f"  50 {i:>2}: {format_time(s)}  (vs PB50 adj: {sign}{delta:.2f}s)  cumulative: {format_time(cum[i-1])}")
    print("\nNotes: Negative=back-half; Positive=fast start; Even=mild closing kick.")

def read_splits(granularity: str) -> list:
    if granularity=="50":
        raw=input("Enter per-50 splits separated by ';': ").strip()
        parts=[p.strip() for p in raw.split(";") if p.strip()]; return [parse_time(p) for p in parts]
    else:
        raw=input("Enter per-100 splits separated by ';': ").strip()
        parts=[p.strip() for p in raw.split(";") if p.strip()]; return [parse_time(p) for p in parts]

def postrace_flow():
    print("\n=== POST-RACE ANALYSIS ===")
    stroke = input("Stroke (Freestyle/Backstroke/Breaststroke/Butterfly/IM): ").strip() or "Freestyle"
    distance = int(input("Event distance (m): ").strip())
    gran = input("Split granularity (50/100): ").strip()
    pb50 = parse_time(input("Your 50m PB: ").strip())
    splits=read_splits(granularity=gran); n_splits=max(1,distance//50); total=sum(splits)
    strategy="even"
    if gran=="50" and len(splits)>=2:
        half=len(splits)//2; first,second=sum(splits[:half]),sum(splits[half:])
        if second < first - 0.01*total: strategy="negative"
        elif first < second - 0.01*total: strategy="positive"
    ideal_fracs=ideal_fractions(n_splits,strategy=strategy); ideal_50=[total*f for f in ideal_fracs]
    if gran=="100":
        est_50=[]; 
        for s100 in splits: est_50 += [s100/2.0, s100/2.0]
        splits_50=est_50[:n_splits]
    else: splits_50=splits[:n_splits]
    print("\nPer-50 analysis:")
    for i in range(n_splits):
        actual = splits_50[i] if i<len(splits_50) else None
        ideal = ideal_50[i]
        if actual is None: 
            print(f"  50 {i+1:>2}: (missing) | ideal {format_time(ideal)}"); continue
        diff=actual-ideal; suggestions=[]; base50=project_50_split(pb50,distance)
        if diff>0.40: suggestions.append("Large loss: turns/streamline/breakout.")
        elif diff>0.20: suggestions.append("Moderate: hold SR & SL, reduce breaths.")
        elif diff<-0.20: suggestions.append("Overcooked: ease early to avoid lactate.")
        if actual>base50+1.0: suggestions.append("Boost mid-pool tempo / stronger kick.")
        if i==0 and actual>base50+0.5: suggestions.append("Start: faster reaction, tighter streamline.")
        if i==n_splits-1 and diff>0.15: suggestions.append("Finish: last 12.5m kick burst, no breath final 5m.")
        tip=" ".join(suggestions) if suggestions else "✓ On plan."
        print(f"  50 {i+1:>2}: actual {format_time(actual)} | ideal {format_time(ideal)} | Δ = {diff:+.2f}s  -> {tip}")
    print("\nMacro:")
    if strategy=="negative": print("- Negative split tendency. Push penultimate 50 a bit more.")
    elif strategy=="positive": print("- Fast start. Hold more for the back half.")
    else: print("- Even pacing detected (~1%). Good control.")

def run_competitive_pacing_cli():
    print("Competitive Pacing — CLI\n")
    mode=input("Select mode: (1) Pre-race  (2) Post-race  -> ").strip()
    if mode=="1" or mode.lower().startswith("pre"): prerace_flow()
    elif mode=="2" or mode.lower().startswith("post"): postrace_flow()
    else: print("Unknown selection. Please choose 1 or 2.")

if __name__ == "__main__":
    run_competitive_pacing_cli()
