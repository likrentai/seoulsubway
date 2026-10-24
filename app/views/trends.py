"""Page 2: ridership trends over time, with route and operator filters."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import settings as S
from app.data import load
from app.theme import CHART_CONFIG, colors, css, style

css()
D = load()
C = colors()
lines = D["lines"].sort_values("line_order")
days = D["daily_network"][["date", "day_type", "holiday_name"]]

st.markdown(f'<h2 style="margin:0">Ridership trends<span class="badge">{S.DATA_BADGE}</span></h2><p class="note" style="margin:0.2rem 0 0">Boardings per day from transit card records, 2015 to 2026. Use the filters to focus on routes or operators.</p>', unsafe_allow_html=True)

# ---------- filters ----------
f1, f2, f3 = st.columns([1.4, 1, 1.6])
routes_all = list(dict.fromkeys(lines["route"]))
operators_all = list(dict.fromkeys(lines["operator_group"]))
routes = f1.multiselect("Routes", routes_all, placeholder="All routes")
operators = f2.multiselect("Operators", operators_all, placeholder="All operators")
dmin = days["date"].min().to_pydatetime()
dmax = days["date"].max().to_pydatetime()
d0, d1 = f3.slider("Period", min_value=dmin, max_value=dmax, value=(dmin, dmax), format="MMM YYYY")

sel = lines.copy()
if routes:
    sel = sel[sel["route"].isin(routes)]
if operators:
    sel = sel[sel["operator_group"].isin(operators)]
if sel.empty:
    st.warning("No line matches this combination of routes and operators. Change the filters.")
    st.stop()
scope = " · ".join(", ".join(x) for x in (routes, operators) if x) or "all routes"


@st.cache_data
def daily_for(line_list):
    """Daily boardings for a set of lines, with day type and holiday name."""
    dl = D["daily_line"]
    d = dl[dl["line_ko"].isin(line_list)].groupby("date", as_index=False)["board"].sum()
    return d.merge(days, on="date", how="left")


all_daily = daily_for(tuple(sel["line_ko"]))
daily = all_daily[(all_daily["date"] >= pd.Timestamp(d0)) & (all_daily["date"] <= pd.Timestamp(d1))]

# ---------- 1. main trend ----------
st.markdown(f'<p class="sec">Boardings per day · {scope}</p>', unsafe_allow_html=True)
view = st.segmented_control("View", ["Daily", "Weekly", "Monthly"], default=S.TREND_DEFAULT_VIEW, label_visibility="collapsed") or S.TREND_DEFAULT_VIEW
fig = go.Figure()
fig.add_vrect(x0=S.COVID_START, x1=S.COVID_END, fillcolor=C["border"], opacity=0.45, line_width=0, annotation_text="COVID-19 rules", annotation_position="top left", annotation_font_color=C["muted"])
if view == "Daily":
    fig.add_scatter(x=daily["date"], y=daily["board"] / 1e6, mode="lines", line=dict(color=C["accent"], width=1), name="Every day", hovertemplate="%{x|%a %d %b %Y}: %{y:.2f} M<extra></extra>")
    hol = daily[daily["day_type"] == "holiday"]
    fig.add_scatter(x=hol["date"], y=hol["board"] / 1e6, mode="markers", marker=dict(color=S.COLOR_WARN, size=6), name="Public holiday", customdata=hol["holiday_name"], hovertemplate="%{x|%a %d %b %Y}: %{y:.2f} M<br>%{customdata}<extra></extra>")
elif view == "Weekly":
    w = daily.set_index("date")["board"].resample("W-MON", label="left", closed="left").mean().reset_index()
    fig.add_scatter(x=w["date"], y=w["board"] / 1e6, mode="lines", line=dict(color=C["accent"], width=1.8), name="Average day in the week", hovertemplate="Week of %{x|%d %b %Y}: %{y:.2f} M<extra></extra>")
else:
    m = daily.assign(month=daily["date"].dt.to_period("M").dt.to_timestamp())
    m_all = m.groupby("month")["board"].mean()
    m_wk = m[m["day_type"] == "weekday"].groupby("month")["board"].mean()
    fig.add_scatter(x=m_all.index, y=m_all / 1e6, mode="lines", line=dict(color=C["muted"], width=1, dash="dot"), name="All days", hovertemplate="%{x|%b %Y}: %{y:.2f} M (all days)<extra></extra>")
    fig.add_scatter(x=m_wk.index, y=m_wk / 1e6, mode="lines", line=dict(color=C["accent"], width=2.5), name="Weekdays", hovertemplate="%{x|%b %Y}: %{y:.2f} M (weekdays)<extra></extra>")
style(fig, 380)
fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.07, x=1, xanchor="right", font=dict(color=C["muted"])))
fig.update_yaxes(title_text="million boardings a day", title_font=dict(color=C["muted"], size=12))
st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")

# ---------- 2. weekday and weekend ----------
st.markdown('<p class="sec">Weekdays and weekends · monthly averages</p>', unsafe_allow_html=True)
m = daily.assign(month=daily["date"].dt.to_period("M").dt.to_timestamp())
wk = m[m["day_type"] == "weekday"].groupby("month")["board"].mean()
we = m[m["day_type"] == "weekend"].groupby("month")["board"].mean()
ratio = (we / wk * 100).dropna()
c1, c2 = st.columns([1.5, 1])
with c1:
    fig = go.Figure()
    fig.add_scatter(x=wk.index, y=wk / 1e6, mode="lines", line=dict(color=C["accent"], width=2), name="Weekday", hovertemplate="%{x|%b %Y}: %{y:.2f} M a weekday<extra></extra>")
    fig.add_scatter(x=we.index, y=we / 1e6, mode="lines", line=dict(color=S.COLOR_GOOD, width=2), name="Weekend day", hovertemplate="%{x|%b %Y}: %{y:.2f} M a weekend day<extra></extra>")
    style(fig, 300)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.1, x=1, xanchor="right", font=dict(color=C["muted"])))
    fig.update_yaxes(title_text="million boardings a day", title_font=dict(color=C["muted"], size=12))
    st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")
with c2:
    fig = go.Figure()
    fig.add_scatter(x=ratio.index, y=ratio, mode="lines", line=dict(color=S.COLOR_WARN, width=2), fill="tozeroy", fillcolor="rgba(245,181,68,0.08)", hovertemplate="%{x|%b %Y}: a weekend day carries %{y:.0f}% of a weekday<extra></extra>")
    style(fig, 300)
    fig.update_yaxes(title_text="weekend day as % of weekday", title_font=dict(color=C["muted"], size=12), range=[max(0, ratio.min() - 10), min(110, ratio.max() + 10)])
    st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")

# ---------- 3. change by route ----------
# Like-for-like: only stations with weekday data in every month of both periods are compared,
# so new stations and stations that left the data do not distort the change.
end = daily["date"].max().to_period("M").to_timestamp()
start = end - pd.DateOffset(months=S.YOY_WINDOW_MONTHS - 1)
prev_start = start - pd.DateOffset(months=S.YOY_WINDOW_MONTHS)
ms = D["monthly_station"]
ms = ms[ms["line_ko"].isin(sel["line_ko"]) & ms["avg_weekday"].notna()].merge(lines[["line_ko", "route"]], on="line_ko")


def station_means(m0, m1):
    """Average weekday boardings per station over the months m0 to m1, for stations with data in every month."""
    w = ms[(ms["month"] >= m0) & (ms["month"] <= m1)]
    n = len(pd.date_range(m0, m1, freq="MS"))
    g = w.groupby(["route", "line_ko", "station_ko"])["avg_weekday"].agg(["mean", "count"])
    return g[g["count"] == n]["mean"]


def route_change(m0, m1, b0, b1):
    a = station_means(m0, m1)
    b = station_means(b0, b1)
    both = pd.concat([a.rename("now"), b.rename("then")], axis=1, join="inner")
    r = both.groupby(level="route").sum()
    return (r["now"] / r["then"] - 1) * 100


vs_prev = route_change(start, end, prev_start, start - pd.DateOffset(months=1))
vs_base = route_change(start, end, pd.Timestamp(year=S.BASELINE_YEAR, month=1, day=1), pd.Timestamp(year=S.BASELINE_YEAR, month=12, day=1))
period = f"{start.strftime('%b %Y')} to {end.strftime('%b %Y')}"
st.markdown(f'<p class="sec">Change by route · average weekday, {period} · same stations in both periods</p>', unsafe_allow_html=True)


def change_bars(series, title):
    s = series.dropna().sort_values()
    col = [S.COLOR_GOOD if v >= 0 else S.COLOR_BAD for v in s]
    fig = go.Figure(go.Bar(x=s, y=s.index, orientation="h", marker_color=col, marker_line_width=0, text=[("0%" if round(v) == 0 else f"{v:+.0f}%") for v in s], textposition="outside", textfont=dict(color=C["muted"]), cliponaxis=False, hovertemplate="%{y}: %{x:+.1f}%<extra></extra>"))
    style(fig, max(260, 26 * len(s) + 40))
    fig.update_layout(margin=dict(l=8, r=40, t=30, b=8), title=dict(text=title, font=dict(size=13, color=C["muted"]), x=0))
    fig.add_vline(x=0, line_color=C["muted"], line_width=1)
    lo = min(s.min(), 0)
    hi = max(s.max(), 0)
    pad = (hi - lo) * 0.18 + 1
    fig.update_xaxes(range=[lo - pad if lo < 0 else lo, hi + pad], ticksuffix="%")
    return fig


c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(change_bars(vs_prev, f"vs the {S.YOY_WINDOW_MONTHS} months before"), config=CHART_CONFIG, width="stretch")
with c2:
    st.plotly_chart(change_bars(vs_base, f"vs {S.BASELINE_YEAR} (stations open in {S.BASELINE_YEAR})"), config=CHART_CONFIG, width="stretch")
st.markdown('<p class="note">Only stations with data in every month of both periods are compared. New stations, and stations that left the card data (for example the Bucheon and Incheon section of Line 7), would otherwise show up as growth or decline that is not about passengers.</p>', unsafe_allow_html=True)

# ---------- 4. calendar ----------
st.markdown('<p class="sec">Calendar · every day of one year</p>', unsafe_allow_html=True)
years = sorted(all_daily["date"].dt.year.unique(), reverse=True)
full_years = [y for y in years if (all_daily["date"].dt.year == y).sum() >= 365]
default_year = S.CALENDAR_DEFAULT_YEAR or (full_years[0] if full_years else years[0])
year = st.columns([1, 4])[0].selectbox("Year", years, index=years.index(default_year))
cal = all_daily[all_daily["date"].dt.year == year].copy()
cal["dow"] = cal["date"].dt.dayofweek
cal["week"] = ((cal["date"] - pd.Timestamp(year=year, month=1, day=1)).dt.days + pd.Timestamp(year=year, month=1, day=1).dayofweek) // 7
z = cal.pivot(index="dow", columns="week", values="board") / 1e6
txt = cal.assign(t=cal["date"].dt.strftime("%a %d %b") + cal["holiday_name"].fillna("").map(lambda h: f"<br>{h}" if h else "")).pivot(index="dow", columns="week", values="t")
month_ticks = cal.groupby(cal["date"].dt.month)["week"].min()
fig = go.Figure(go.Heatmap(z=z.values, x=z.columns, y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], text=txt.values, hovertemplate="%{text}: %{z:.2f} M<extra></extra>", colorscale=[[0, C["panel"]], [0.5, "#1B6F8F"], [1, C["accent"]]], xgap=3, ygap=3, colorbar=dict(title=dict(text="M a day", font=dict(color=C["muted"], size=11)), tickfont=dict(color=C["muted"]), thickness=10)))
style(fig, 260)
fig.update_xaxes(tickvals=list(month_ticks.values), ticktext=[pd.Timestamp(year=2000, month=k, day=1).strftime("%b") for k in month_ticks.index], showgrid=False)
fig.update_yaxes(autorange="reversed", showgrid=False)
st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")
st.markdown('<p class="note">Darker squares are quieter days. Public holidays, the summer and the COVID-19 waves show up as patterns. Hover over a square for its date, holiday name and boardings.</p>', unsafe_allow_html=True)
st.markdown('<p class="note">Source: Seoul Open Data Plaza, daily card ridership by line and station. Weekday means Monday to Friday without public holidays. A route groups the KORAIL and Seoul Metro sections of one coloured line (for example Line 1 includes the Gyeongbu and Gyeongwon Lines).</p>', unsafe_allow_html=True)
