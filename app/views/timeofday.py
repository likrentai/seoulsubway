"""Page 4: time of day. Network rhythm, home and work stations, and the hourly profile of any station (Seoul Metro, 2024)."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import settings as S
from app.data import load
from app.theme import CHART_CONFIG, colors, css, style, tile

css()
D = load()
C = colors()
lines = D["lines"].sort_values("line_order")
line_en = lines.set_index("line_ko")["line_en"]
hl = D["hourly_line"]
hs = D["hourly_station"]
HOUR_LABEL = {h: ("before 06" if h == 5 else "after 24" if h == 24 else f"{h:02d}:00") for h in range(5, 25)}
DAY_NAMES = {"weekday": "Weekday", "weekend": "Weekend day", "holiday": "Public holiday"}

st.markdown(f'<h2 style="margin:0">Time of day<span class="badge">{S.DATA_BADGE}</span></h2><p class="note" style="margin:0.2rem 0 0">How the city moves through the day: gate counts by hour at Seoul Metro stations (Lines 1 to 8) in 2024 (April left out, see the note at the bottom).</p>', unsafe_allow_html=True)

# ---------- filter ----------
metro = [l for l in lines["line_ko"] if l in set(hl["line_ko"])]
f1, f2 = st.columns([2, 1])
pick_lines = f1.multiselect("Lines", metro, format_func=lambda l: line_en.get(l, l), placeholder="All Seoul Metro lines (1 to 8)")
sel = pick_lines or metro
h = hl[hl["line_ko"].isin(sel)].groupby(["day_type", "gate", "hour"], as_index=False)["avg_per_day"].sum()

# ---------- tiles ----------
wk_b = h[(h["day_type"] == "weekday") & (h["gate"] == "board")].set_index("hour")["avg_per_day"]
we_b = h[(h["day_type"] == "weekend") & (h["gate"] == "board")].set_index("hour")["avg_per_day"]
total = wk_b.sum()
peak_hour = wk_b.idxmax()
am = wk_b[wk_b.index.isin(S.AM_PEAK_HOURS)].sum() / total * 100
pm = wk_b[wk_b.index.isin(S.PM_PEAK_HOURS)].sum() / total * 100
we_peak = we_b.idxmax()
am_label = f"{S.AM_PEAK_HOURS[0]:02d}:00 to {S.AM_PEAK_HOURS[-1] + 1:02d}:00"
pm_label = f"{S.PM_PEAK_HOURS[0]:02d}:00 to {S.PM_PEAK_HOURS[-1] + 1:02d}:00"
t = st.columns(4)
t[0].markdown(tile("Busiest weekday hour", HOUR_LABEL[peak_hour], f"{wk_b.max() / 1e3:,.0f}k boardings, {wk_b.max() / total * 100:.0f}% of the day"), unsafe_allow_html=True)
t[1].markdown(tile("Morning peak share", f"{am:.0f}%", f"of weekday boardings, {am_label}"), unsafe_allow_html=True)
t[2].markdown(tile("Evening peak share", f"{pm:.0f}%", f"of weekday boardings, {pm_label}"), unsafe_allow_html=True)
t[3].markdown(tile("Busiest weekend hour", HOUR_LABEL[we_peak], f"{we_b.max() / 1e3:,.0f}k boardings, weekend days are {we_b.sum() / total * 100:.0f}% of a weekday"), unsafe_allow_html=True)

# ---------- 1. rhythm ----------
st.markdown('<p class="sec">The daily rhythm · boardings per hour, average day</p>', unsafe_allow_html=True)
fig = go.Figure()
for dt, col, width in [("weekday", C["accent"], 3), ("weekend", S.COLOR_GOOD, 2), ("holiday", S.COLOR_WARN, 1.5)]:
    s = h[(h["day_type"] == dt) & (h["gate"] == "board")].sort_values("hour")
    fig.add_scatter(x=s["hour"], y=s["avg_per_day"] / 1e3, customdata=[HOUR_LABEL[x] for x in s["hour"]], mode="lines+markers", line=dict(color=col, width=width, shape="spline"), marker=dict(size=5), name=DAY_NAMES[dt], hovertemplate="%{customdata}: %{y:,.0f}k boardings<extra>" + DAY_NAMES[dt] + "</extra>")
for hrs in (S.AM_PEAK_HOURS, S.PM_PEAK_HOURS):
    fig.add_vrect(x0=hrs[0] - 0.5, x1=hrs[-1] + 0.5, fillcolor=C["border"], opacity=0.4, line_width=0, layer="below")
style(fig, 340)
fig.update_xaxes(tickvals=list(HOUR_LABEL), ticktext=list(HOUR_LABEL.values()))
fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.08, x=1, xanchor="right", font=dict(color=C["muted"])))
fig.update_yaxes(title_text="thousand boardings in the hour", title_font=dict(color=C["muted"], size=12))
st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")
st.markdown('<p class="note">Shaded: the morning and evening peaks used in the tiles. Weekends have no morning peak; travel builds up to a broad afternoon high.</p>', unsafe_allow_html=True)

# ---------- 2. home and work stations ----------
st.markdown(f'<p class="sec">Home and work stations · weekday morning peak, {am_label}</p>', unsafe_allow_html=True)
m = hs[(hs["line_ko"].isin(sel)) & (hs["day_type"] == "weekday") & (hs["hour"].isin(S.AM_PEAK_HOURS))]
m = m.pivot_table(index=["line_ko", "station_code", "station_label"], columns="gate", values="avg_per_day", aggfunc="sum").reset_index()
m["taps"] = m["board"] + m["alight"]
m["share"] = m["board"] / m["taps"]
m["type"] = "mixed"
m.loc[m["share"] >= S.HOME_SHARE, "type"] = "home"
m.loc[m["share"] <= S.WORK_SHARE, "type"] = "work"
m["name"] = [f"{l} · {line_en.get(k, k)}" for l, k in zip(m["station_label"], m["line_ko"])]
TYPE_COL = {"home": S.COLOR_HOME, "work": S.COLOR_WORK, "mixed": C["muted"]}
TYPE_TEXT = {"home": "Home: mostly boarding in the morning", "work": "Work: mostly arriving in the morning", "mixed": "Mixed"}
c1, c2 = st.columns([1.3, 1])
with c1:
    fig = go.Figure()
    for ty in ["mixed", "home", "work"]:
        d = m[m["type"] == ty]
        fig.add_scatter(x=d["alight"], y=d["board"], mode="markers", marker=dict(color=TYPE_COL[ty], size=7, opacity=0.85, line=dict(width=0)), name=TYPE_TEXT[ty], text=d["name"], hovertemplate="%{text}<br>%{y:,.0f} board, %{x:,.0f} get off<extra></extra>")
    mx = max(m["board"].max(), m["alight"].max()) * 1.2
    fig.add_scatter(x=[100, mx], y=[100, mx], mode="lines", line=dict(color=C["border"], dash="dot"), hoverinfo="skip", showlegend=False)
    style(fig, 420)
    fig.update_xaxes(type="log", title_text="people getting off, morning peak (log scale)", title_font=dict(color=C["muted"], size=12))
    fig.update_yaxes(type="log", title_text="people boarding, morning peak (log scale)", title_font=dict(color=C["muted"], size=12))
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.2, x=0, font=dict(color=C["muted"])))
    st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")
with c2:
    big = m[m["taps"] >= S.MIN_MORNING_TAPS]

    def lst(df, value, col, title, verb):
        d = df.iloc[::-1]
        fig = go.Figure(go.Bar(x=d[value] * 100, y=d["name"], orientation="h", marker_color=col, marker_line_width=0, text=[f"{v * 100:.0f}%" for v in d[value]], textposition="inside", insidetextanchor="end", textfont=dict(color=C["bg"]), customdata=d["taps"], hovertemplate="%{y}<br>%{x:.0f}% of %{customdata:,.0f} morning taps are " + verb + "<extra></extra>"))
        style(fig, 210)
        fig.update_xaxes(range=[0, 100], ticksuffix="%", showticklabels=False)
        fig.update_layout(margin=dict(l=8, r=8, t=26, b=4), title=dict(text=title, font=dict(size=13, color=C["muted"]), x=0))
        return fig

    big = big.assign(arrive=1 - big["share"])
    st.plotly_chart(lst(big.nlargest(7, "share"), "share", S.COLOR_HOME, "Most 'home': share of morning taps that are boardings", "boardings"), config=CHART_CONFIG, width="stretch")
    st.plotly_chart(lst(big.nlargest(7, "arrive"), "arrive", S.COLOR_WORK, "Most 'work': share of morning taps that are people getting off", "people getting off"), config=CHART_CONFIG, width="stretch")
n_type = m["type"].value_counts()
st.markdown(f'<p class="note">Each dot is a station on one line. Above the dotted line more people board than get off in the morning, typical of homes; below it more people arrive, typical of offices and schools. {n_type.get("home", 0)} stations are "home" ({S.HOME_SHARE:.0%} or more of morning taps are boardings), {n_type.get("work", 0)} are "work" ({S.WORK_SHARE:.0%} or less) and {n_type.get("mixed", 0)} are mixed. The lists only include stations with at least {S.MIN_MORNING_TAPS:,} morning taps a weekday.</p>', unsafe_allow_html=True)

# ---------- 3. station profile ----------
st.markdown('<p class="sec">Hourly profile of one station</p>', unsafe_allow_html=True)
opts = hs[["line_ko", "station_code", "station_ko", "station_label"]].drop_duplicates().copy()
opts["name"] = [f"{l} · {line_en.get(k, k)}" for l, k in zip(opts["station_label"], opts["line_ko"])]
opts = opts.sort_values("name")
names = list(opts["name"])
default = opts[opts["station_ko"] == S.DEFAULT_PROFILE_STATION]["name"]
g1, g2 = st.columns([2, 1])
pick = g1.selectbox("Station (type to search, in English or Korean)", names, index=names.index(default.iloc[0]) if len(default) else 0)
day = g2.segmented_control("Day type", list(DAY_NAMES), default="weekday", format_func=lambda d: DAY_NAMES[d]) or "weekday"
code = opts[opts["name"] == pick]["station_code"].iloc[0]
one = hs[(hs["station_code"] == code) & (hs["day_type"] == day)].sort_values("hour")
fig = go.Figure()
for gate, col, label in [("board", C["accent"], "Boarding"), ("alight", S.COLOR_WARN, "Getting off")]:
    d = one[one["gate"] == gate]
    fig.add_bar(x=[HOUR_LABEL[x] for x in d["hour"]], y=d["avg_per_day"], marker_color=col, marker_line_width=0, name=label, hovertemplate="%{x}: %{y:,.0f} " + label.lower() + "<extra></extra>")
style(fig, 320)
fig.update_layout(barmode="group", bargap=0.25, showlegend=True, legend=dict(orientation="h", y=1.1, x=1, xanchor="right", font=dict(color=C["muted"])))
fig.update_yaxes(title_text=f"people in the hour, average {DAY_NAMES[day].lower()}", title_font=dict(color=C["muted"], size=12))
st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")
st.markdown('<p class="note">Source: Seoul Metro hourly boardings and alightings by station, 2024 (data.go.kr). April 2024 is left out: in the source file its 13:00 hour is about ten times too high on every day. Without April, the hourly totals match the daily card data used on the other pages to within 0.5%.</p>', unsafe_allow_html=True)
