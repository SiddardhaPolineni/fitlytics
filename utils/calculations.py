"""
Pure calculation helpers – no Streamlit dependencies.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import date, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Streak helpers
# ---------------------------------------------------------------------------

def calc_streak(series: pd.Series) -> tuple[int, int]:
    """
    Given a boolean Series (True = goal met that day), return
    (current_streak, longest_streak).
    The series must be sorted ascending by date.
    """
    values = series.values.tolist()
    current = 0
    longest = 0
    running = 0
    for v in values:
        if v:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    # current streak = tail of the series
    for v in reversed(values):
        if v:
            current += 1
        else:
            break
    return current, longest


def workout_streak(workouts: pd.DataFrame) -> tuple[int, int]:
    """Current and longest consecutive workout days."""
    workout_days = workouts["date"].dt.date.unique()
    if len(workout_days) == 0:
        return 0, 0
    start = min(workout_days)
    end = date.today()
    all_days = pd.date_range(start, end, freq="D").date
    met = pd.Series([d in set(workout_days) for d in all_days])
    return calc_streak(met)


def sleep_streak(health: pd.DataFrame, target_hours: float = 7.0) -> tuple[int, int]:
    met = health.set_index("date")["sleep_hours"] >= target_hours
    met = met.sort_index()
    return calc_streak(met)


def steps_streak(health: pd.DataFrame, target: int = 10_000) -> tuple[int, int]:
    met = health.set_index("date")["steps"] >= target
    met = met.sort_index()
    return calc_streak(met)


# ---------------------------------------------------------------------------
# Recovery score
# ---------------------------------------------------------------------------

def recovery_score(health: pd.DataFrame) -> tuple[float, str, list[str]]:
    """
    Returns (score 0-100, status label, list of insight strings).

    Scoring model (weighted average of 3 normalised sub-scores):
      - Sleep quality  40 %   (8 h = 100, 5 h = 0, clipped)
      - HRV            35 %   (60 ms = 100, 20 ms = 0)
      - Resting HR     25 %   (45 bpm = 100, 80 bpm = 0, inverted)

    We use the last 7 days.
    """
    recent = health.tail(7).copy()
    if recent.empty:
        return 50.0, "Unknown", ["Not enough data."]

    # --- Sleep sub-score ---
    avg_sleep = recent["sleep_hours"].mean()
    sleep_score = np.clip((avg_sleep - 5) / (8 - 5) * 100, 0, 100)

    # --- HRV sub-score ---
    avg_hrv = recent["hrv_ms"].mean()
    hrv_score = np.clip((avg_hrv - 20) / (60 - 20) * 100, 0, 100)

    # --- Resting HR sub-score (lower is better) ---
    avg_rhr = recent["resting_hr"].mean()
    rhr_score = np.clip((80 - avg_rhr) / (80 - 45) * 100, 0, 100)

    score = 0.40 * sleep_score + 0.35 * hrv_score + 0.25 * rhr_score

    # Status label
    if score >= 80:
        status = "Optimal"
    elif score >= 65:
        status = "Good"
    elif score >= 50:
        status = "Moderate"
    elif score >= 35:
        status = "Low"
    else:
        status = "Poor"

    # Insights
    insights: list[str] = []
    if avg_sleep < 7:
        insights.append(f"Average sleep is {avg_sleep:.1f} h — aim for 7-8 h to improve recovery.")
    else:
        insights.append(f"Sleep is solid at {avg_sleep:.1f} h/night — keep it up.")

    if avg_hrv < 40:
        insights.append(f"HRV ({avg_hrv:.0f} ms) is below optimal — consider a lighter training day.")
    else:
        insights.append(f"HRV ({avg_hrv:.0f} ms) indicates good autonomic recovery.")

    if avg_rhr > 65:
        insights.append(f"Resting HR ({avg_rhr:.0f} bpm) is elevated — monitor for overtraining.")
    else:
        insights.append(f"Resting HR ({avg_rhr:.0f} bpm) is in a healthy range.")

    return round(score, 1), status, insights


# ---------------------------------------------------------------------------
# Personal Records
# ---------------------------------------------------------------------------

def find_prs(workouts: pd.DataFrame) -> pd.DataFrame:
    """
    For each exercise, find the date of each new 1-rep-max equivalent PR
    (using Epley formula: 1RM = w * (1 + reps/30)).
    Returns a DataFrame with columns:
      exercise, date, weight_kg, reps, estimated_1rm, is_all_time_pr
    """
    results = []
    for exercise, group in workouts.groupby("exercise"):
        group = group.sort_values("date").copy()
        group["est_1rm"] = group["weight_kg"] * (1 + group["reps"] / 30)
        running_max = 0.0
        for _, row in group.iterrows():
            if row["est_1rm"] > running_max:
                running_max = row["est_1rm"]
                results.append({
                    "exercise": exercise,
                    "date": row["date"],
                    "weight_kg": row["weight_kg"],
                    "reps": int(row["reps"]),
                    "estimated_1rm": round(row["est_1rm"], 1),
                })
    if not results:
        return pd.DataFrame()
    df = pd.DataFrame(results).sort_values("date", ascending=False)
    # Mark all-time PRs (latest PR per exercise = current all-time)
    df["is_all_time_pr"] = ~df.duplicated(subset="exercise", keep="first")
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Training Volume
# ---------------------------------------------------------------------------

def weekly_volume(workouts: pd.DataFrame) -> pd.DataFrame:
    df = workouts.copy()
    df["week"] = df["date"].dt.to_period("W").apply(lambda p: p.start_time)
    return df.groupby("week")["volume"].sum().reset_index().rename(columns={"volume": "total_volume"})


def monthly_volume(workouts: pd.DataFrame) -> pd.DataFrame:
    df = workouts.copy()
    df["month"] = df["date"].dt.to_period("M").apply(lambda p: p.start_time)
    return df.groupby("month")["volume"].sum().reset_index().rename(columns={"volume": "total_volume"})


def muscle_group_volume(workouts: pd.DataFrame) -> pd.DataFrame:
    return (
        workouts.groupby("muscle_group")["volume"]
        .sum()
        .reset_index()
        .rename(columns={"volume": "total_volume"})
        .sort_values("total_volume", ascending=False)
    )


# ---------------------------------------------------------------------------
# Weight trend & projection
# ---------------------------------------------------------------------------

def weight_moving_averages(health: pd.DataFrame) -> pd.DataFrame:
    df = health[["date", "weight_kg"]].copy().sort_values("date")
    df["ma7"] = df["weight_kg"].rolling(7, min_periods=1).mean()
    df["ma30"] = df["weight_kg"].rolling(30, min_periods=1).mean()
    return df


def weight_projection(health: pd.DataFrame, days_ahead: int = 30) -> pd.DataFrame:
    """Linear regression on last 30 days → project `days_ahead` into the future."""
    df = health[["date", "weight_kg"]].tail(30).copy()
    if len(df) < 5:
        return pd.DataFrame()
    x = np.arange(len(df))
    y = df["weight_kg"].values
    coeffs = np.polyfit(x, y, 1)
    slope, intercept = coeffs
    last_date = df["date"].max()
    future_dates = [last_date + timedelta(days=i + 1) for i in range(days_ahead)]
    future_weights = [slope * (len(df) + i) + intercept for i in range(days_ahead)]
    proj = pd.DataFrame({"date": future_dates, "projected_weight": future_weights})
    return proj


# ---------------------------------------------------------------------------
# Goal progress helpers
# ---------------------------------------------------------------------------

def goal_progress(goals: pd.DataFrame, health: pd.DataFrame, workouts: pd.DataFrame) -> pd.DataFrame:
    """
    Augment the goals DataFrame with computed progress fields.
    """
    rows = []
    latest_weight = health["weight_kg"].iloc[-1] if not health.empty else None
    latest_steps = health["steps"].iloc[-1] if not health.empty else None

    for _, g in goals.iterrows():
        current = g["current_value"]

        # Auto-update from live data where possible
        if g["goal_type"] == "weight_loss" and latest_weight is not None:
            current = latest_weight
        elif g["goal_type"] == "strength":
            ex_data = workouts[workouts["exercise"] == g["metric"]]
            if not ex_data.empty:
                current = ex_data["weight_kg"].max()
        elif g["goal_type"] == "cardio" and g["metric"] == "steps" and latest_steps is not None:
            current = latest_steps

        start = g["start_value"]
        target = g["target_value"]
        # Progress % (handles both increasing and decreasing goals)
        total_change_needed = abs(target - start)
        change_so_far = abs(current - start)
        if total_change_needed == 0:
            pct = 100.0
        else:
            pct = min(change_so_far / total_change_needed * 100, 100)

        # Estimated completion via linear extrapolation
        days_elapsed = (date.today() - g["start_date"].date()).days
        if change_so_far > 0 and days_elapsed > 0:
            rate_per_day = change_so_far / days_elapsed
            remaining = total_change_needed - change_so_far
            if rate_per_day > 0 and remaining > 0:
                days_to_go = remaining / rate_per_day
                est_completion = date.today() + timedelta(days=days_to_go)
            else:
                est_completion = date.today()
        else:
            est_completion = g["target_date"].date()

        rows.append({
            **g.to_dict(),
            "current_value": current,
            "pct_complete": round(pct, 1),
            "est_completion": est_completion,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Weekly summary
# ---------------------------------------------------------------------------

def weekly_summary(health: pd.DataFrame, workouts: pd.DataFrame) -> dict:
    """Produce a summary dict for the last 7 days vs prior 7 days."""
    today = health["date"].max().date()
    week_start = today - timedelta(days=6)
    prev_start = week_start - timedelta(days=7)

    this_week_h = health[health["date"].dt.date >= week_start]
    prev_week_h = health[(health["date"].dt.date >= prev_start) & (health["date"].dt.date < week_start)]

    this_week_w = workouts[workouts["date"].dt.date >= week_start]
    prev_week_w = workouts[(workouts["date"].dt.date >= prev_start) & (workouts["date"].dt.date < week_start)]

    def safe_mean(df, col):
        return df[col].mean() if not df.empty else 0

    def pct_change(curr, prev):
        if prev == 0:
            return 0
        return round((curr - prev) / prev * 100, 1)

    avg_weight_now = safe_mean(this_week_h, "weight_kg")
    avg_weight_prev = safe_mean(prev_week_h, "weight_kg")
    vol_now = this_week_w["volume"].sum()
    vol_prev = prev_week_w["volume"].sum()
    workouts_now = this_week_w["date"].dt.date.nunique()
    sleep_now = safe_mean(this_week_h, "sleep_hours")
    sleep_prev = safe_mean(prev_week_h, "sleep_hours")
    steps_now = safe_mean(this_week_h, "steps")
    steps_prev = safe_mean(prev_week_h, "steps")
    hrv_now = safe_mean(this_week_h, "hrv_ms")
    hrv_prev = safe_mean(prev_week_h, "hrv_ms")

    wins = []
    watchlist = []
    recommendations = []

    weight_delta = avg_weight_now - avg_weight_prev
    if weight_delta < -0.3:
        wins.append(f"Lost {abs(weight_delta):.1f} kg this week — on track with your weight goal.")
    elif weight_delta > 0.5:
        watchlist.append(f"Weight increased by {weight_delta:.1f} kg — review nutrition.")

    vol_chg = pct_change(vol_now, vol_prev)
    if vol_chg > 5:
        wins.append(f"Training volume up {vol_chg}% vs last week — great progression.")
    elif vol_chg < -15:
        watchlist.append(f"Training volume dropped {abs(vol_chg)}% vs last week.")

    if workouts_now >= 4:
        wins.append(f"Completed {workouts_now} workout days this week — excellent consistency.")
    elif workouts_now <= 2:
        watchlist.append(f"Only {workouts_now} workout days this week — try to hit 3-4.")

    if sleep_now >= 7.5:
        wins.append(f"Averaging {sleep_now:.1f} h sleep — recovery is well supported.")
    elif sleep_now < 6.5:
        watchlist.append(f"Sleep averaged only {sleep_now:.1f} h — prioritise rest.")
        recommendations.append("Aim for 7-9 hours of sleep to maximise muscle recovery and performance.")

    if hrv_now > hrv_prev:
        wins.append(f"HRV improved to {hrv_now:.0f} ms (+{hrv_now-hrv_prev:.0f} ms) — good recovery trend.")
    if steps_now >= 10_000:
        wins.append(f"Hit daily step goal with an average of {steps_now:,.0f} steps/day.")

    if not recommendations:
        recommendations.append("Maintain current training intensity and monitor recovery signals.")
        recommendations.append("Consider adding a deload week after every 4-6 weeks of progressive overload.")

    return {
        "avg_weight_now": avg_weight_now,
        "avg_weight_prev": avg_weight_prev,
        "weight_delta": weight_delta,
        "vol_now": vol_now,
        "vol_prev": vol_prev,
        "vol_pct_change": vol_chg,
        "workouts_this_week": workouts_now,
        "sleep_avg": sleep_now,
        "steps_avg": steps_now,
        "hrv_avg": hrv_now,
        "wins": wins,
        "watchlist": watchlist,
        "recommendations": recommendations,
    }
