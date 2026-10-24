"""Page 5: crowding. Heatmap by station and half hour, trend by line, most crowded trains and weekend hot spots (Seoul Metro, 2023 Q4 to 2026 Q2)."""

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


@st.cache_resource
def crowding_table():
    """The crowding table with text columns, prepared once and shared by every visit (read only)."""
    t = D["crowding_station"].copy()
    for col in ["quarter", "day_type", "line_ko", "station_label", "direction", "slot"]:
        t[col] = t[col].astype(str)
    return t


@st.cache_data
def peak_by_line(day_type):
    """Highest crowding per line and quarter for one day type."""
    t = crowding_table()
    return t[t["day_type"] == day_type].groupby(["line_ko", "quarter"])["crowding_pct"].max().reset_index()


cs = crowding_table()
SLOTS = list(dict.fromkeys(D["crowding_profile"].sort_values("slot_order")["slot"]))
DAY_NAMES = {"weekday": "Weekday", "saturday": "Saturday", "sunday": "Sunday"}
q_label = lambda q: f"{q[:4]} Q{q[-1]}"
people = lambda pct: pct / 100 * S.PEOPLE_AT_100_PCT


def direction_name(line_ko, d):
    return S.DIRECTION_NAMES.get(line_ko, {}).get(d, d)


st.markdown(f'<h2 style="margin:0">Crowding<span class="badge">{S.DATA_BADGE}</span></h2><p class="note" style="margin:0.2rem 0 0">How full the trains are, by station, direction and half hour, from Seoul Metro\'s quarterly crowding figures (Lines 1 to 8). 100% means about {S.PEOPLE_AT_100_PCT} people in one car: every seat taken and the aisles comfortably full. 34% means every seat taken.</p>', unsafe_allow_html=True)

# ---------- controls ----------
quarters = sorted(cs["quarter"].unique(), reverse=True)
f1, f2 = st.columns([1, 1.6])
quarter = f1.selectbox("Quarter", quarters, format_func=q_label)
day = f2.segmented_control("Day type", list(DAY_NAMES), default="weekday", format_func=lambda d: DAY_NAMES[d]) or "weekday"
q = cs[(cs["quarter"] == quarter) & (cs["day_type"] == day)].dropna(subset=["crowding_pct"])

# ---------- tiles ----------
top = q.loc[q["crowding_pct"].idxmax()]
prev_q = str(pd.Period(quarter, freq="Q") - 4)
prev = cs[(cs["quarter"] == prev_q) & (cs["day_type"] == day)]["crowding_pct"].max()
full = (q["crowding_pct"] >= S.CROWD_FULL).sum()
by_line = q.groupby("line_ko")["crowding_pct"].max()
t = st.columns(4)
prev_text = f"vs {q_label(prev_q)} · " if pd.notna(prev) else ""
t[0].markdown(tile("Peak crowding", f"{top['crowding_pct']:.0f}%", f"{prev_text}≈ {people(top['crowding_pct']):.0f} people per car", (top["crowding_pct"] - prev) if pd.notna(prev) else None, f"{top['crowding_pct'] - prev:+.0f} pt" if pd.notna(prev) else ""), unsafe_allow_html=True)
t[1].markdown(tile("Most crowded train", top["station_label"], f"{line_en.get(top['line_ko'])} · {direction_name(top['line_ko'], top['direction'])} · {top['slot']}", small=True), unsafe_allow_html=True)
t[2].markdown(tile(f"Half hours at {S.CROWD_FULL}% or more", f"{full:,}", f"of {len(q):,} station, direction and half-hour slots ({full / len(q) * 100:.1f}%)"), unsafe_allow_html=True)
t[3].markdown(tile("Most crowded line", line_en.get(by_line.idxmax()), f"peak {by_line.max():.0f}% · lowest peak: {line_en.get(by_line.idxmin())} {by_line.min():.0f}%", small=True), unsafe_allow_html=True)

# ---------- 1. heatmap ----------
st.markdown(f'<p class="sec">Where and when trains are full · {q_label(quarter)} · {DAY_NAMES[day].lower()}</p>', unsafe_allow_html=True)
crowd_lines = set(cs["line_ko"].unique())
metro = [l for l in lines["line_ko"] if l in crowd_lines]
g1, g2 = st.columns([1, 1.6])
line = g1.selectbox("Line", metro, index=metro.index(S.DEFAULT_CROWD_LINE) if S.DEFAULT_CROWD_LINE in metro else 0, format_func=lambda l: line_en.get(l, l))
dirs = sorted(q[q["line_ko"] == line]["direction"].unique())
busiest = q[q["line_ko"] == line].groupby("direction")["crowding_pct"].max().idxmax() if dirs else None
direction = g2.segmented_control("Direction", dirs, default=busiest, format_func=lambda d: direction_name(line, d)) or busiest
h = cs[(cs["quarter"] == quarter) & (cs["day_type"] == day) & (cs["line_ko"] == line) & (cs["direction"] == direction)]
order = h.drop_duplicates("station_code").sort_values("station_code")
z = h.pivot_table(index="station_code", columns="slot", values="crowding_pct").reindex(index=order["station_code"], columns=SLOTS)
cd = [[f"{people(v):.0f}" if pd.notna(v) else "" for v in row] for row in z.values]
scale = [[0, C["panel"]], [0.17, "#123A5A"], [0.34, "#1B6F8F"], [0.5, C["accent"]], [0.62, S.COLOR_WARN], [0.75, S.COLOR_BAD], [1, "#FF2D55"]]
fig = go.Figure(go.Heatmap(z=z.values, x=SLOTS, y=list(order["station_label"]), customdata=cd, zmin=0, zmax=200, colorscale=scale, xgap=1, ygap=1, hovertemplate="%{y}<br>%{x}: %{z:.0f}% · about %{customdata} people per car<extra></extra>", colorbar=dict(title=dict(text="crowding %", font=dict(color=C["muted"], size=11)), tickfont=dict(color=C["muted"]), thickness=10, tickvals=[0, 34, 100, 150, 200], ticktext=["0", "34 seats full", "100", "150", "200"])))
style(fig, max(380, 17 * len(order) + 80))
fig.update_xaxes(tickvals=["06:00", "08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00", "00:00"], showgrid=False, side="top")
fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=11))
st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")
st.markdown('<p class="note">Rows are stations in station-number order; each square is the average crowding of trains leaving that station in that half hour. Blue is comfortable, cyan is busy, amber is crowded and red means more than about 240 people in one car.</p>', unsafe_allow_html=True)

# ---------- 2. trend by line ----------
st.markdown(f'<p class="sec">Peak crowding by line, quarter by quarter · {DAY_NAMES[day].lower()}</p>', unsafe_allow_html=True)
tr = peak_by_line(day)
all_q = [str(p) for p in pd.period_range(min(quarters), max(quarters), freq="Q")]
fig = go.Figure()
series = C["series"]
for i, l in enumerate(metro):
    d = tr[tr["line_ko"] == l].set_index("quarter").reindex(all_q)
    fig.add_scatter(x=[q_label(x) for x in all_q], y=d["crowding_pct"], mode="lines+markers", connectgaps=False, line=dict(color=series[i % len(series)], width=3 if l == line else 1.5), marker=dict(size=6 if l == line else 4), name=line_en.get(l), hovertemplate="%{x}: %{y:.0f}%<extra>" + line_en.get(l) + "</extra>")
style(fig, 340)
fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.15, x=0, font=dict(color=C["muted"])))
fig.update_yaxes(title_text="highest crowding in the quarter (%)", title_font=dict(color=C["muted"], size=12))
st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")
st.markdown(f'<p class="note">The line chosen for the heatmap is drawn thicker. 2024 Q3 was never published, so the lines have a gap there.</p>', unsafe_allow_html=True)

# ---------- 3. most crowded and weekend hot spots ----------
c1, c2 = st.columns(2)


def bars(df, color, title):
    d = df.iloc[::-1]
    names = [f"{s} · {line_en.get(l).replace(' (Seoul Metro section)', '')} · {direction_name(l, r)} · {t}" for s, l, r, t in zip(d["station_label"], d["line_ko"], d["direction"], d["slot"])]
    fig = go.Figure(go.Bar(x=d["crowding_pct"], y=names, orientation="h", marker_color=color, marker_line_width=0, text=[f"{v:.0f}%" for v in d["crowding_pct"]], textposition="inside", insidetextanchor="end", textfont=dict(color=C["bg"]), customdata=people(d["crowding_pct"]), hovertemplate="%{y}<br>%{x:.0f}%, about %{customdata:.0f} people per car<extra></extra>"))
    style(fig, 30 * len(d) + 60)
    fig.update_layout(margin=dict(l=8, r=8, t=30, b=8), title=dict(text=title, font=dict(size=13, color=C["muted"]), x=0))
    fig.update_xaxes(ticksuffix="%")
    return fig


with c1:
    st.plotly_chart(bars(q.nlargest(S.N_TOP_CROWDED, "crowding_pct"), S.COLOR_BAD, f"Most crowded trains · {q_label(quarter)} · {DAY_NAMES[day].lower()}"), config=CHART_CONFIG, width="stretch")
with c2:
    keys = ["line_ko", "station_code", "station_label", "direction", "slot"]
    wk = cs[(cs["quarter"] == quarter) & (cs["day_type"] == "weekday")][keys + ["crowding_pct"]].rename(columns={"crowding_pct": "weekday"})
    we = cs[(cs["quarter"] == quarter) & (cs["day_type"].isin(["saturday", "sunday"]))].dropna(subset=["crowding_pct"])
    we = we.loc[we.groupby(keys)["crowding_pct"].idxmax()]
    hot = we.merge(wk, on=keys)
    hot = hot[hot["crowding_pct"] > hot["weekday"] + 10].nlargest(S.N_TOP_CROWDED, "crowding_pct")
    if len(hot):
        hot = hot.assign(slot=[f"{DAY_NAMES[d][:3]} {s}" for d, s in zip(hot["day_type"], hot["slot"])])
        st.plotly_chart(bars(hot, S.COLOR_HOME, f"Weekend hot spots · busier than the same weekday half hour"), config=CHART_CONFIG, width="stretch")
    else:
        st.info("No weekend half hour in this quarter is clearly busier than the same weekday half hour.")
st.markdown('<p class="note">Weekend hot spots are station, direction and half-hour slots where a Saturday or Sunday is more crowded than a weekday by more than 10 points: often concerts, sports events or leisure travel. Source: Seoul Metro crowding by station and half hour, via Seoul Open Data Plaza.</p>', unsafe_allow_html=True)
