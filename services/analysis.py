\
from typing import Dict, List
import statistics as stats

def analyze_pace(lap_times_sec: List[float], rest_intervals_sec: List[float]=None, heart_rates: List[int]=None) -> Dict:
    report = {}
    if not lap_times_sec:
        return {"error": "No lap times provided."}

    mean_pace = sum(lap_times_sec)/len(lap_times_sec)
    stdev = stats.pstdev(lap_times_sec) if len(lap_times_sec) > 1 else 0.0
    cv = (stdev/mean_pace)*100 if mean_pace>0 else 0.0

    comments = []
    if cv <= 2.0:
        comments.append("Excellent pacing consistency (CV ≤ 2%).")
    elif cv <= 4.0:
        comments.append("Good pacing consistency (CV ≤ 4%). Aim for tighter control on mid reps.")
    else:
        comments.append("Pacing variability is high; consider shorter reps or stricter send-offs.")

    if rest_intervals_sec:
        avg_rest = sum(rest_intervals_sec)/len(rest_intervals_sec)
        comments.append(f"Average rest: {avg_rest:.1f}s.")
        if avg_rest < 10:
            comments.append("Rest may be too short—risk of form breakdown.")
        elif avg_rest > 45:
            comments.append("Rest may be too long—consider reducing to maintain stimulus.")

    if heart_rates:
        avg_hr = sum(heart_rates)/len(heart_rates)
        comments.append(f"Average HR: {avg_hr:.0f} bpm.")
        if avg_hr < 120:
            comments.append("Intensity may be too low for aerobic adaptation; increase pace or reduce rest.")
        elif avg_hr > 180:
            comments.append("HR very high—ensure proper recovery and technique quality.")

    report.update({
        "mean_pace_sec": round(mean_pace,2),
        "stdev_sec": round(stdev,2),
        "cv_percent": round(cv,2),
        "insights": comments
    })
    return report
