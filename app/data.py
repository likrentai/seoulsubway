"""Loading the summary files and the calculations behind the KPI tiles."""

import pandas as pd
import streamlit as st

from app import settings as S


@st.cache_data
def load():
    d = {}
    for name in ["daily_network", "daily_line", "monthly_network", "monthly_route", "monthly_station", "crowding_profile", "crowding_peaks", "hourly_line", "hourly_station", "crowding_station"]:
        d[name] = pd.read_parquet(S.DATA / f"{name}.parquet")
    d["lines"] = pd.read_csv(S.DATA / "lines.csv")
    d["stations"] = pd.read_csv(S.DATA / "stations.csv")
    d["operations"] = pd.read_csv(S.DATA / "operations.csv")
    return d


def same_month(df, month, years_back):
    """Row of a monthly table for the same month some years earlier (None if missing)."""
    target = month - pd.DateOffset(years=years_back)
    rows = df[df["month"] == target]
    return rows.iloc[0] if len(rows) else None


def baseline_month(month):
    """The same calendar month in the baseline year."""
    return pd.Timestamp(year=S.BASELINE_YEAR, month=month.month, day=1)


def quarter_for(month, quarters):
    """Crowding quarter to show for a month: its own quarter if published, otherwise the latest earlier one. None before the first quarter."""
    q = str(pd.Period(month, freq="Q"))
    earlier = sorted(x for x in quarters if x <= q)
    if not earlier:
        return None, False
    return earlier[-1], earlier[-1] == q


def pct_change(new, old):
    if old is None or pd.isna(old) or old == 0 or pd.isna(new):
        return None
    return (new / old - 1) * 100
