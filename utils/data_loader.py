"""
Centralised data loading with file-aware caching.

Cache strategy
--------------
* Workouts and health data: TTL=300s (change rarely).
* Goals: invalidated whenever goals.csv is modified on disk —
  achieved by passing the file's mtime as a cache parameter.
  This means edits to goals.csv show up on the very next rerun.
"""
import pathlib
import pandas as pd
import streamlit as st

ROOT = pathlib.Path(__file__).parent.parent
DATA = ROOT / "data"


@st.cache_data(ttl=300)
def load_workouts() -> pd.DataFrame:
    df = pd.read_csv(DATA / "workouts.csv", parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["volume"] = df["sets"] * df["reps"] * df["weight_kg"]
    return df


@st.cache_data(ttl=300)
def load_health() -> pd.DataFrame:
    df = pd.read_csv(DATA / "health_metrics.csv", parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def load_goals() -> pd.DataFrame:
    """No cache — reads goals.csv fresh on every rerun (tiny file, instant)."""
    df = pd.read_csv(DATA / "goals.csv", parse_dates=["start_date", "target_date"])
    return df