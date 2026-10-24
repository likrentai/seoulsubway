"""Page 6: service. What Seoul Metro runs on Lines 1 to 8 (March 2024), and how it compares with ridership and crowding in the same year."""

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
ops = D["operations"].copy()
year = S.SERVICE_YEAR


@st.cache_data
def line_figures(y):
    """Average weekday boardings per line (card data), peak-hour boardings (hourly data) and peak crowding (crowding data) for one year."""
    days = D["daily_network"][["date", "day_type"]]
    dl = D["daily_line"].merge(days, on="date")
    dl = dl[(dl["date"].dt.year == y) & (dl["day_type"] == "weekday")]
    board = dl.groupby("line_ko")["board"].mean()
    hl = D["hourly_line"]
    peak = hl[(hl["day_type"] == "weekday") & (hl["gate"] == "board") & (hl["hour"] == S.PEAK_HOUR)].set_index("line_ko")["avg_per_day"]
    cs = D["crowding_station"]
    cw = cs[(cs["quarter"].astype(str).str.startswith(str(y))) & (cs["day_type"].astype(str) == "weekday")]
    crowd = cw.groupby([cw["line_ko"].astype(str), cw["quarter"].astype(str)], observed=True)["crowding_pct"].max().groupby(level=0).mean()
    quarters = sorted(cw["quarter"].astype(str).unique())
    return board, peak, crowd, quarters


board, peak, crowd, crowd_quarters = line_figures(year)
ops["name"] = ops["line_ko"].map(line_en).str.replace(" (Seoul Metro section)", "", regex=False)
ops["board_weekday"] = ops["line_ko"].map(board)
ops["peak_board"] = ops["line_ko"].map(peak)
ops["peak_crowd"] = ops["line_ko"].map(crowd)
ops["trains_per_hour"] = 60 / ops["headway_peak_min"]
ops["capacity_hour"] = ops["trains_per_hour"] * ops["cars_per_trainset"] * S.PEOPLE_AT_100_PCT
ops["per_train_km"] = ops["board_weekday"] / ops["train_km_weekday"]
ops["per_trip"] = ops["board_weekday"] / ops["trips_weekday"]
ops["per_peak_train"] = ops["peak_board"] / (2 * ops["trains_per_hour"])
ops["cars_in_service_share"] = ops["trainsets"] * ops["cars_per_trainset"] / ops["cars_owned"]

st.markdown(f'<h2 style="margin:0">Service<span class="badge">{S.DATA_BADGE}</span></h2><p class="note" style="margin:0.2rem 0 0">What Seoul Metro runs on Lines 1 to 8 (operating figures as of March 2024), compared with ridership and crowding in {year}. Line 1 here is only the short Seoul Metro section from Seoul Station to Cheongnyangni, so its ratios are not comparable with the other lines.</p>', unsafe_allow_html=True)

# ---------- tiles ----------
t = st.columns(5)
t[0].markdown(tile("Route length", f"{ops['length_km'].sum():.0f} km", "Lines 1 to 8, Seoul Metro sections"), unsafe_allow_html=True)
t[1].markdown(tile("Stations", f"{ops['stations'].sum():.0f}", "a transfer station counts once per line"), unsafe_allow_html=True)
t[2].markdown(tile("Trains", f"{ops['trainsets'].sum():.0f}", f"{ops['cars_owned'].sum():,.0f} cars in the fleet"), unsafe_allow_html=True)
t[3].markdown(tile("Trips a weekday", f"{ops['trips_weekday'].sum():,.0f}", f"{ops['trips_holiday'].sum():,.0f} on a holiday"), unsafe_allow_html=True)
t[4].markdown(tile("Train-km a weekday", f"{ops['train_km_weekday'].sum() / 1e3:,.0f}k", f"about {ops['train_km_weekday'].sum() / 40075:.1f} times around the Earth"), unsafe_allow_html=True)

# ---------- 1. line table ----------
st.markdown('<p class="sec">Line by line · operating figures, March 2024</p>', unsafe_allow_html=True)
tbl = pd.DataFrame({
    "Line": ops["name"],
    "Route": [f"{S.ROUTE_EN.get(l, '')} ({k})" if l in S.ROUTE_EN else k for l, k in zip(ops["line_ko"], ops["section"])],
    "Length (km)": ops["length_km"],
    "Stations": ops["stations"].astype(int),
    "End to end (min)": ops["end_to_end_min"],
    "Average speed (km/h)": ops["average_speed_kmh"],
    "Peak headway (min)": ops["headway_peak_min"],
    "Off-peak headway (min)": ops["headway_offpeak_min"],
    "Trips a weekday": ops["trips_weekday"].astype(int),
    "Trains": ops["trainsets"].astype(int),
    "Cars per train": ops["cars_per_trainset"].astype(int),
})
st.dataframe(tbl, hide_index=True, width="stretch", column_config={
    "Length (km)": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=float(tbl["Length (km)"].max())),
    "Average speed (km/h)": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=float(tbl["Average speed (km/h)"].max())),
    "Trips a weekday": st.column_config.ProgressColumn(format="%d", min_value=0, max_value=int(tbl["Trips a weekday"].max())),
})
notes = ops[ops["note"].notna() & (ops["note"] != "")]
st.markdown('<p class="note">' + " · ".join(f"{n}: {x}" for n, x in zip(notes["name"], notes["note"])) + ". Headway is the time between trains.</p>", unsafe_allow_html=True)

# ---------- 2. efficiency ----------
st.markdown(f'<p class="sec">How hard each line works · average weekday, {year}</p>', unsafe_allow_html=True)
eff = ops.dropna(subset=["per_train_km"])
eff = eff[eff["line_ko"] != "1호선"]


def hbar(df, col, title, fmt, color):
    d = df.sort_values(col)
    fig = go.Figure(go.Bar(x=d[col], y=d["name"], orientation="h", marker_color=color, marker_line_width=0, text=[fmt(v) for v in d[col]], textposition="outside", textfont=dict(color=C["muted"]), cliponaxis=False, hovertemplate="%{y}: %{x:,.1f}<extra></extra>"))
    style(fig, 300)
    fig.update_layout(margin=dict(l=8, r=50, t=30, b=8), title=dict(text=title, font=dict(size=13, color=C["muted"]), x=0))
    return fig


c1, c2, c3 = st.columns(3)
with c1:
    st.plotly_chart(hbar(eff, "per_train_km", "Boardings per train-km", lambda v: f"{v:.0f}", C["accent"]), config=CHART_CONFIG, width="stretch")
with c2:
    st.plotly_chart(hbar(eff, "per_trip", "Boardings per trip", lambda v: f"{v:,.0f}", S.COLOR_GOOD), config=CHART_CONFIG, width="stretch")
with c3:
    st.plotly_chart(hbar(eff.dropna(subset=["per_peak_train"]), "per_peak_train", f"People boarding per train, {S.PEAK_HOUR:02d}:00 to {S.PEAK_HOUR + 1:02d}:00", lambda v: f"{v:,.0f}", S.COLOR_WARN), config=CHART_CONFIG, width="stretch")
st.markdown(f'<p class="note">Boardings come from the {year} card data (average weekday) and the peak hour from the {year} hourly gate counts; trips and train-km from the March 2024 operating figures. "People boarding per train" divides the boardings in the peak hour by the trains running in both directions in that hour. Line 1 is left out of these three charts (see the note at the top).</p>', unsafe_allow_html=True)

# ---------- 3. capacity and crowding ----------
st.markdown(f'<p class="sec">Capacity and crowding at the morning peak · {year}</p>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.2])
with c1:
    d = ops.sort_values("capacity_hour")
    fig = go.Figure(go.Bar(x=d["capacity_hour"] / 1e3, y=d["name"], orientation="h", marker_color=C["accent"], marker_line_width=0, text=[f"{v / 1e3:.1f}k" for v in d["capacity_hour"]], textposition="outside", textfont=dict(color=C["muted"]), cliponaxis=False, customdata=list(zip(d["trains_per_hour"], d["cars_per_trainset"])), hovertemplate="%{y}: %{x:.1f}k people an hour<br>%{customdata[0]:.0f} trains an hour × %{customdata[1]:.0f} cars × " + str(S.PEOPLE_AT_100_PCT) + " people<extra></extra>"))
    style(fig, 320)
    fig.update_layout(margin=dict(l=8, r=50, t=30, b=8), title=dict(text=f"Peak capacity per direction (thousand people an hour at 100%)", font=dict(size=13, color=C["muted"]), x=0))
    st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")
with c2:
    d = ops.dropna(subset=["peak_crowd"])
    spots = ["top center", "middle left", "middle right", "bottom center"]
    d = d.sort_values(["trains_per_hour", "peak_crowd"], ascending=[True, False])
    d["pos"] = [spots[i % len(spots)] for i in d.groupby("trains_per_hour").cumcount()]
    fig = go.Figure(go.Scatter(x=d["trains_per_hour"], y=d["peak_crowd"], mode="markers+text", text=d["name"], textposition=list(d["pos"]), textfont=dict(color=C["text"], size=12), cliponaxis=False, marker=dict(size=(d["board_weekday"] / d["board_weekday"].max()) * 45 + 10, color=C["accent"], opacity=0.55, line=dict(color=C["accent"], width=1)), customdata=list(zip(d["board_weekday"] / 1e3, d["cars_per_trainset"])), hovertemplate="%{text}<br>%{x:.0f} trains an hour at the peak, %{customdata[1]:.0f} cars each<br>highest crowding %{y:.0f}%<br>%{customdata[0]:,.0f}k boardings a weekday<extra></extra>"))
    style(fig, 320)
    fig.update_layout(margin=dict(l=8, r=8, t=30, b=8), title=dict(text="More trains, less crowding? (bubble size: weekday boardings)", font=dict(size=13, color=C["muted"]), x=0))
    fig.update_xaxes(title_text="trains an hour at the peak (60 ÷ headway)", title_font=dict(color=C["muted"], size=12), range=[d["trains_per_hour"].min() - 3, d["trains_per_hour"].max() + 4])
    fig.update_yaxes(range=[d["peak_crowd"].min() - 8, d["peak_crowd"].max() + 16])
    fig.update_yaxes(title_text="highest crowding in the quarter (%)", title_font=dict(color=C["muted"], size=12))
    st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")
qtxt = ", ".join(f"{q[:4]} Q{q[-1]}" for q in crowd_quarters)
hi = d.loc[d["peak_crowd"].idxmax()]
lo = d.loc[d["peak_crowd"].idxmin()]
small = d.loc[d["capacity_hour"].idxmin()]
summary = f"Most crowded: {hi['name']} at {hi['peak_crowd']:.0f}%, with a train every {hi['headway_peak_min']:g} minutes. Least crowded: {lo['name']} at {lo['peak_crowd']:.0f}%. {small['name']} has the smallest peak capacity ({small['capacity_hour'] / 1e3:.1f}k people an hour: {small['cars_per_trainset']:.0f}-car trains every {small['headway_peak_min']:g} minutes) and reaches {small['peak_crowd']:.0f}%."
st.markdown(f'<p class="note">{summary} Capacity counts {S.PEOPLE_AT_100_PCT} people per car (100% crowding) on every train in the peak hour, in one direction. Highest crowding is the average of each quarter\'s weekday maximum for the line ({qtxt}). Sources: Seoul Metro train operation status (March 2024), card ridership, hourly gate counts and crowding data via Seoul Open Data Plaza and data.go.kr.</p>', unsafe_allow_html=True)
