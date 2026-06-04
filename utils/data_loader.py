"""
Centralised data loading with caching.
All paths are relative to the project root (one level up from this file).
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
    # Volume = sets × reps × weight (bodyweight exercises count as 0)
    df["volume"] = df["sets"] * df["reps"] * df["weight_kg"]
    return df


@st.cache_data(ttl=300)
def load_health() -> pd.DataFrame:
    df = pd.read_csv(DATA / "health_metrics.csv", parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


@st.cache_data(ttl=300)
def load_goals() -> pd.DataFrame:
    df = pd.read_csv(DATA / "goals.csv", parse_dates=["start_date", "target_date"])
    return df
