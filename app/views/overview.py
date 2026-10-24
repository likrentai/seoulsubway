"""Page 1: the one-screen KPI overview."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import settings as S
from app.data import baseline_month, load, pct_change, quarter_for, same_month
from app.theme import CHART_CONFIG, colors, css, style, tile

css()
D = load()
C = colors()
net = D["monthly_network"]
months = sorted(net["month"], reverse=True)

# ---------- header and month selector ----------
h1, h2 = st.columns([3, 1], vertical_alignment="bottom")
with h1:
    st.markdown(f'<h2 style="margin:0">{S.APP_TITLE}<span class="badge">{S.DATA_BADGE}</span></h2><p class="note" style="margin:0.2rem 0 0">{S.APP_SUBTITLE}</p>', unsafe_allow_html=True)
with h2:
    month = st.selectbox("Month", months, index=0, format_func=lambda m: m.strftime("%B %Y"))

row = net[net["month"] == month].iloc[0]
prev = same_month(net, month, 1)
base = net[net["month"] == baseline_month(month)]
base = base.iloc[0] if len(base) else None

st_m = D["monthly_station"]
st_now = st_m[(st_m["month"] == month) & (st_m["weekdays"] >= S.MIN_WEEKDAYS)]
st_prev = st_m[(st_m["month"] == month - pd.DateOffset(years=1)) & (st_m["weekdays"] >= S.MIN_WEEKDAYS)]

# ---------- KPI values ----------
wk = row["avg_weekday"]
wk_yoy = pct_change(wk, prev["avg_weekday"]) if prev is not None else None
recovery = wk / base["avg_weekday"] * 100 if (base is not None and month.year > S.BASELINE_YEAR) else None

busiest = st_now.sort_values("avg_weekday", ascending=False).iloc[0]

growth = st_now.merge(st_prev[["line_ko", "station_ko", "avg_weekday"]], on=["line_ko", "station_ko"], suffixes=("", "_prev"))
growth = growth[growth["avg_weekday_prev"] >= S.MIN_BASE_GROWTH]
growth["chg"] = (growth["avg_weekday"] / growth["avg_weekday_prev"] - 1) * 100
top_growth = growth.sort_values("chg", ascending=False).iloc[0] if len(growth) else None

we_ratio = row["avg_weekend"] / wk * 100
we_prev = prev["avg_weekend"] / prev["avg_weekday"] * 100 if prev is not None else None

prof = D["crowding_profile"]
peaks = D["crowding_peaks"]
quarter, own_quarter = quarter_for(month, prof["quarter"].unique())
if quarter:
    pk = peaks[(peaks["quarter"] == quarter) & (peaks["day_type"] == "weekday")].iloc[0]

first = net.iloc[0]
line_en = D["lines"].set_index("line_ko")["line_en"]
DIRECTION = {"up": "up line", "down": "down line", "inner": "inner loop", "outer": "outer loop"}

# ---------- tiles: row 1 ----------
st.markdown('<p class="sec">Key figures · average weekday (Monday to Friday, no public holidays)</p>', unsafe_allow_html=True)
t = st.columns(4)
t[0].markdown(tile("Weekday boardings", f"{wk / 1e6:.2f} M", f"vs {month.year - 1} · all days {row['avg_all_days'] / 1e6:.2f} M", wk_yoy, f"{wk_yoy:+.1f}%" if wk_yoy is not None else ""), unsafe_allow_html=True)
if recovery is not None:
    t[1].markdown(tile(f"Recovery vs {S.BASELINE_YEAR}", f"{recovery:.0f}%", f"{month.strftime('%b')} {S.BASELINE_YEAR}: {base['avg_weekday'] / 1e6:.2f} M a weekday"), unsafe_allow_html=True)
else:
    t[1].markdown(tile(f"Recovery vs {S.BASELINE_YEAR}", "n/a", f"{month.year} is in the baseline period"), unsafe_allow_html=True)
t[2].markdown(tile("Busiest station", busiest["station_label"], f"{busiest['avg_weekday'] / 1e3:.1f}k boardings a weekday", small=True), unsafe_allow_html=True)
if top_growth is not None:
    t[3].markdown(tile("Fastest-growing station", top_growth["station_label"], f"vs {month.year - 1} · {top_growth['avg_weekday'] / 1e3:.1f}k a weekday", top_growth["chg"], f"{top_growth['chg']:+.0f}%", small=True), unsafe_allow_html=True)
else:
    t[3].markdown(tile("Fastest-growing station", "n/a", "needs a year earlier to compare"), unsafe_allow_html=True)

# ---------- tiles: row 2 ----------
t = st.columns(4)
we_delta = we_ratio - we_prev if we_prev is not None else None
t[0].markdown(tile("Weekend vs weekday", f"{we_ratio:.0f}%", f"pt vs {month.year - 1}", we_delta, f"{we_delta:+.1f}" if we_delta is not None else ""), unsafe_allow_html=True)
if quarter:
    q_note = "" if own_quarter else " (latest published)"
    t[1].markdown(tile("Peak crowding", f"{pk['crowding_pct']:.0f}%", f"≈ {pk['crowding_pct'] / 100 * S.PEOPLE_AT_100_PCT:.0f} people per car · {quarter[:4]} Q{quarter[-1]}{q_note}"), unsafe_allow_html=True)
    t[2].markdown(tile("Most crowded train", pk["station_label"], f"{line_en.get(pk['line_ko'], pk['line_ko'])} · {DIRECTION.get(pk['direction'], pk['direction'])} · {pk['slot']}", small=True), unsafe_allow_html=True)
else:
    t[1].markdown(tile("Peak crowding", "n/a", "crowding data starts in late 2023"), unsafe_allow_html=True)
    t[2].markdown(tile("Most crowded train", "n/a", "crowding data starts in late 2023"), unsafe_allow_html=True)
t[3].markdown(tile("Stations (by line)", f"{row['stations']:.0f}", f"since {first['month'].strftime('%b %Y')} · a transfer station counts once per line", row["stations"] - first["stations"], f"{row['stations'] - first['stations']:+.0f}"), unsafe_allow_html=True)

# ---------- trend and meters ----------
st.markdown('<p class="sec">Trend and meters</p>', unsafe_allow_html=True)
c1, c2 = st.columns([2.2, 1])
with c1:
    fig = go.Figure()
    fig.add_vrect(x0=S.COVID_START, x1=S.COVID_END, fillcolor=C["border"], opacity=0.45, line_width=0, annotation_text="COVID-19 rules", annotation_position="top left", annotation_font_color=C["muted"])
    fig.add_scatter(x=net["month"], y=net["avg_all_days"] / 1e6, mode="lines", line=dict(color=C["muted"], width=1, dash="dot"), name="All days", hovertemplate="%{x|%b %Y}: %{y:.2f} M (all days)<extra></extra>")
    fig.add_scatter(x=net["month"], y=net["avg_weekday"] / 1e6, mode="lines", line=dict(color=C["accent"], width=2.5), name="Weekdays", hovertemplate="%{x|%b %Y}: %{y:.2f} M (weekdays)<extra></extra>")
    fig.add_scatter(x=[month], y=[wk / 1e6], mode="markers", marker=dict(color=C["accent"], size=11, line=dict(color=C["bg"], width=2)), hoverinfo="skip", showlegend=False)
    style(fig, 300)
    fig.update_yaxes(title_text="million boardings a day", title_font=dict(color=C["muted"], size=12))
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.08, x=1, xanchor="right", font=dict(color=C["muted"])))
    st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")
with c2:
    def gauge(value, title, vmax, color, ref=100, height=160):
        g = go.Figure(go.Indicator(mode="gauge+number", value=value, number=dict(suffix="%", valueformat=".0f", font=dict(size=28, color=C["text"])), title=dict(text=title, font=dict(size=13, color=C["muted"])), gauge=dict(axis=dict(range=[0, vmax], tickcolor=C["muted"], tickfont=dict(color=C["muted"], size=10)), bar=dict(color=color, thickness=0.75), bgcolor=C["panel"], borderwidth=0, threshold=dict(line=dict(color=C["text"], width=2), thickness=0.9, value=ref))))
        style(g, height)
        g.update_layout(margin=dict(l=24, r=24, t=44, b=4))
        return g
    if recovery is not None:
        st.plotly_chart(gauge(recovery, f"Recovery vs {S.BASELINE_YEAR} (weekdays)", S.GAUGE_RECOVERY_MAX, S.COLOR_GOOD), config=CHART_CONFIG, width="stretch")
    else:
        st.info(f"Recovery is measured from {S.BASELINE_YEAR + 1} onwards.")
    if quarter:
        st.plotly_chart(gauge(pk["crowding_pct"], f"Peak crowding ({quarter[:4]} Q{quarter[-1]})", S.GAUGE_CROWD_MAX, S.COLOR_WARN if pk["crowding_pct"] < 150 else S.COLOR_BAD), config=CHART_CONFIG, width="stretch")
    else:
        st.info("Crowding data starts in late 2023.")

# ---------- routes and crowding strip ----------
c1, c2 = st.columns(2)
with c1:
    st.markdown(f'<p class="sec">Routes · weekday boardings and % of {month.strftime("%b")} {S.BASELINE_YEAR}</p>', unsafe_allow_html=True)
    rt = D["monthly_route"]
    now = rt[rt["month"] == month].nlargest(S.N_ROUTES, "avg_weekday")
    old = rt[rt["month"] == baseline_month(month)].set_index("route")["avg_weekday"]
    now = now.assign(base=now["route"].map(old)).iloc[::-1]
    now["pct"] = now["avg_weekday"] / now["base"] * 100
    label = now["pct"].map(lambda p: "new" if pd.isna(p) else f"{p:.0f}%") if month.year > S.BASELINE_YEAR else now["pct"].map(lambda p: "")
    col = now["pct"].map(lambda p: C["muted"] if pd.isna(p) or month.year <= S.BASELINE_YEAR else (S.COLOR_GOOD if p >= 105 else (S.COLOR_BAD if p < 95 else C["text"])))
    fig = go.Figure(go.Bar(x=now["avg_weekday"] / 1e3, y=now["route"], orientation="h", marker_color=C["accent"], marker_line_width=0, text=label, textposition="outside", textfont=dict(color=list(col)), cliponaxis=False, hovertemplate="%{y}: %{x:,.0f}k a weekday<extra></extra>"))
    style(fig, 320)
    fig.update_xaxes(title_text="thousand boardings a weekday", title_font=dict(color=C["muted"], size=12))
    fig.update_layout(margin=dict(l=8, r=48, t=8, b=8))
    st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")
with c2:
    if quarter:
        st.markdown(f'<p class="sec">Crowding through a weekday · network average · {quarter[:4]} Q{quarter[-1]} · 100% ≈ {S.PEOPLE_AT_100_PCT} people per car</p>', unsafe_allow_html=True)
        p = prof[(prof["quarter"] == quarter) & (prof["day_type"] == "weekday")].sort_values("slot_order")
        bar_col = p["avg_pct"].map(lambda v: S.COLOR_BAD if v >= S.CROWD_VERY else (S.COLOR_WARN if v >= S.CROWD_BUSY else C["accent"]))
        fig = go.Figure(go.Bar(x=p["slot"], y=p["avg_pct"], marker_color=list(bar_col), marker_line_width=0, customdata=p["max_pct"], hovertemplate="%{x}: average %{y:.0f}%, highest %{customdata:.0f}%<extra></extra>"))
        style(fig, 320)
        fig.update_yaxes(title_text="crowding %", title_font=dict(color=C["muted"], size=12))
        fig.update_xaxes(tickvals=["05:30", "08:00", "12:00", "18:00", "00:30"])
        st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")
    else:
        st.markdown('<p class="sec">Crowding through a weekday</p>', unsafe_allow_html=True)
        st.info("Crowding data from Seoul Metro starts in the fourth quarter of 2023. Choose a later month to see it.")

st.markdown(f'<p class="note">Sources: Seoul Open Data Plaza (daily card ridership by line and station, Seoul Metro crowding by half hour). Weekday means Monday to Friday without public holidays. Crowding covers Seoul Metro Lines 1 to 8 only. Station names: official English names where published, otherwise automatic romanisation.</p>', unsafe_allow_html=True)
