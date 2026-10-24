"""Page 3: stations. Rankings, gainers and losers since 2019, new stations and a station detail view."""

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
ms = D["monthly_station"].merge(lines[["line_ko", "route", "operator_group"]], on="line_ko", how="left")
ms = ms[ms["avg_weekday"].notna()]
last_month = ms["month"].max()

st.markdown(f'<h2 style="margin:0">Stations<span class="badge">{S.DATA_BADGE}</span></h2><p class="note" style="margin:0.2rem 0 0">Busiest stations, biggest changes since {S.BASELINE_YEAR}, new stations and a closer look at any station. A transfer station counts once per line, as in the card data.</p>', unsafe_allow_html=True)

# ---------- controls ----------
latest_start = last_month - pd.DateOffset(months=11)
periods = {f"Latest 12 months ({latest_start.strftime('%b %Y')} to {last_month.strftime('%b %Y')})": (latest_start, last_month)}
for y in sorted(ms["month"].dt.year.unique(), reverse=True):
    if (ms["month"].dt.year == y).any() and ms[ms["month"].dt.year == y]["month"].nunique() == 12:
        periods[str(y)] = (pd.Timestamp(year=y, month=1, day=1), pd.Timestamp(year=y, month=12, day=1))
f1, f2, f3, f4 = st.columns([1.5, 1.3, 0.7, 1])
period_name = f1.selectbox("Period", list(periods))
routes = f2.multiselect("Routes", list(dict.fromkeys(lines["route"])), placeholder="All routes")
top_n = f3.number_input("Stations shown", min_value=5, max_value=40, value=S.TOP_N_DEFAULT, step=5)
combine = f4.toggle("Combine lines at a station", value=False, help="Count a transfer station once, with the boardings of all its lines added together.")
p0, p1 = periods[period_name]
view = ms if not routes else ms[ms["route"].isin(routes)]


def station_period(df, m0, m1, full=False):
    """Average weekday boardings per line and station over months m0 to m1 (weighted by weekdays). full=True keeps only stations with data in every month."""
    w = df[(df["month"] >= m0) & (df["month"] <= m1)].copy()
    w["sum"] = w["avg_weekday"] * w["weekdays"]
    g = w.groupby(["line_ko", "station_ko"]).agg(total=("sum", "sum"), wd=("weekdays", "sum"), months=("month", "nunique"), label=("station_label", "first"), route=("route", "first"))
    g["avg"] = g["total"] / g["wd"]
    if full:
        g = g[g["months"] == len(pd.date_range(m0, m1, freq="MS"))]
    return g


def name(row_label, line_ko):
    return f"{row_label} · {line_en.get(line_ko, line_ko)}"


short = lines.set_index("line_ko")["route"]


def place_key(df):
    """Key for a whole station: the base name, plus the line for names shared by two different places."""
    return df["station_ko"].where(~df["station_ko"].isin(S.SEPARATE_NAMES), df["station_ko"] + "|" + df["line_ko"])


def place_period(df, m0, m1):
    """Average weekday boardings per whole station (all its lines added), the set of lines, and whether every line has data in every month."""
    g = station_period(df, m0, m1).reset_index()
    g["place"] = place_key(g)
    n = len(pd.date_range(m0, m1, freq="MS"))
    out = g.groupby("place").agg(avg=("avg", "sum"), label=("label", "first"), lines=("line_ko", lambda x: frozenset(x)), full=("months", lambda m: bool((m == n).all())))
    out["routes"] = out["lines"].map(lambda ls: ", ".join(sorted(dict.fromkeys(short.get(l, l) for l in ls))))
    return out


# ---------- 1. top stations ----------
if combine:
    now = place_period(view, p0, p1)
    top = now.sort_values("avg", ascending=False).head(int(top_n)).reset_index()
    top["name"] = [f"{l} · {r}" for l, r in zip(top["label"], top["routes"])]
else:
    now = station_period(view, p0, p1)
    top = now.sort_values("avg", ascending=False).head(int(top_n)).reset_index()
    top["name"] = [name(l, k) for l, k in zip(top["label"], top["line_ko"])]
st.markdown(f'<p class="sec">Busiest stations · average weekday boardings · {period_name}</p>', unsafe_allow_html=True)
t = top.iloc[::-1]
fig = go.Figure(go.Bar(x=t["avg"] / 1e3, y=t["name"], orientation="h", marker_color=C["accent"], marker_line_width=0, text=[f"{v / 1e3:.1f}k" for v in t["avg"]], textposition="outside", textfont=dict(color=C["muted"]), cliponaxis=False, hovertemplate="%{y}: %{x:.1f}k a weekday<extra></extra>"))
style(fig, max(300, 24 * len(t) + 40))
fig.update_layout(margin=dict(l=8, r=50, t=8, b=8))
fig.update_xaxes(title_text="thousand boardings a weekday", title_font=dict(color=C["muted"], size=12))
st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")

# ---------- 2. gainers and losers ----------
b0 = pd.Timestamp(year=S.BASELINE_YEAR, month=1, day=1)
b1 = pd.Timestamp(year=S.BASELINE_YEAR, month=12, day=1)
st.markdown(f'<p class="sec">Biggest changes · {period_name} vs {S.BASELINE_YEAR} · whole stations, average weekday</p>', unsafe_allow_html=True)
if p0.year <= S.BASELINE_YEAR:
    st.info(f"Choose a period after {S.BASELINE_YEAR} to compare with {S.BASELINE_YEAR}.")
else:
    a = place_period(view, p0, p1)
    b = place_period(view, b0, b1)
    both = a.join(b[["avg", "lines", "full"]], rsuffix="_base", how="inner")
    both = both[(both["lines"] == both["lines_base"]) & both["full"] & both["full_base"]]
    both = both.rename(columns={"avg_base": "base"})
    both = both[both["base"] >= S.MIN_BASE_CHANGE].reset_index()
    both["chg"] = (both["avg"] / both["base"] - 1) * 100
    both["name"] = [f"{l} · {r}" for l, r in zip(both["label"], both["routes"])]

    def change_chart(df, color, title):
        d = df.iloc[::-1]
        fig = go.Figure(go.Bar(x=d["chg"], y=d["name"], orientation="h", marker_color=color, marker_line_width=0, text=[f"{v:+.0f}%" for v in d["chg"]], textposition="outside", textfont=dict(color=C["muted"]), cliponaxis=False, customdata=list(zip(d["base"] / 1e3, d["avg"] / 1e3)), hovertemplate="%{y}<br>%{customdata[0]:.1f}k to %{customdata[1]:.1f}k a weekday (%{x:+.1f}%)<extra></extra>"))
        style(fig, max(280, 26 * len(d) + 50))
        lo = min(d["chg"].min(), 0)
        hi = max(d["chg"].max(), 0)
        pad = (hi - lo) * 0.2 + 1
        fig.update_xaxes(range=[lo - pad if lo < 0 else 0, hi + pad if hi > 0 else 0], ticksuffix="%")
        fig.update_layout(margin=dict(l=8, r=40, t=30, b=8), title=dict(text=title, font=dict(size=13, color=C["muted"]), x=0))
        return fig

    st.plotly_chart(change_chart(both.nlargest(S.N_GAINERS, "chg"), S.COLOR_GOOD, "Biggest gainers"), config=CHART_CONFIG, width="stretch")
    st.plotly_chart(change_chart(both.nsmallest(S.N_GAINERS, "chg"), S.COLOR_BAD, "Biggest losers"), config=CHART_CONFIG, width="stretch")
    st.markdown(f'<p class="note">Whole stations (all their lines added together) are compared, and only stations whose lines did not change between the two periods, with data in every month and at least {S.MIN_BASE_CHANGE:,} boardings a weekday in {S.BASELINE_YEAR}: {len(both)} stations. When a new line opens at a station, the card data books part of its passengers to the new line, so those stations are left out. Some changes still reflect passengers moving to a nearby new line that is not in this data (for example Guri, after Line 8 reached it in 2024). Hover over a bar for the numbers behind the %.</p>', unsafe_allow_html=True)

# ---------- 3. new stations ----------
stn = D["stations"].copy()
stn["first_day"] = pd.to_datetime(stn["first_day"])
first_data = ms["month"].min()
new = stn[stn["first_day"] > first_data + pd.DateOffset(days=31)].copy()
if routes:
    new = new[new["line_ko"].isin(lines[lines["route"].isin(routes)]["line_ko"])]
latest = station_period(ms, latest_start, last_month)["avg"]
new["latest"] = [latest.get((l, s)) for l, s in zip(new["line_ko"], new["station_ko"])]
new = new.dropna(subset=["latest"]).sort_values("first_day", ascending=False)
st.markdown(f'<p class="sec">New stations since {first_data.strftime("%B %Y")} · {len(new)} in the data</p>', unsafe_allow_html=True)
tbl = pd.DataFrame({"Station": new["station_label"], "Line": new["line_ko"].map(line_en), "Data from": new["first_day"].dt.strftime("%b %Y"), "Boardings a weekday, latest 12 months": new["latest"].round(0).astype(int)})
st.dataframe(tbl, hide_index=True, width="stretch", height=min(420, 36 * len(tbl) + 40), column_config={"Boardings a weekday, latest 12 months": st.column_config.ProgressColumn(format="%d", min_value=0, max_value=int(tbl["Boardings a weekday, latest 12 months"].max()) if len(tbl) else 1)})
st.markdown('<p class="note">"Data from" is the first month a station appears in the card data, which is usually its opening month. A few stations appear because a section changed operator or name.</p>', unsafe_allow_html=True)

# ---------- 4. station detail ----------
st.markdown('<p class="sec">Station detail</p>', unsafe_allow_html=True)
opts = stn.dropna(subset=["first_day"]).copy()
opts["name"] = [name(l, k) for l, k in zip(opts["station_label"], opts["line_ko"])]
opts = opts.sort_values("station_en")
default = opts.index[opts["station_ko"] == S.DEFAULT_STATION]
pick = st.selectbox("Station (type to search, in English or Korean)", list(opts["name"]), index=list(opts.index).index(default[0]) if len(default) else 0)
one = opts[opts["name"] == pick].iloc[0]
hist = ms[(ms["line_ko"] == one["line_ko"]) & (ms["station_ko"] == one["station_ko"])].sort_values("month")
line_now = station_period(ms[ms["line_ko"] == one["line_ko"]], latest_start, last_month).sort_values("avg", ascending=False)
key = (one["line_ko"], one["station_ko"])
cur = line_now["avg"].get(key)
rank = list(line_now.index).index(key) + 1 if key in line_now.index else None
base_one = station_period(ms[(ms["line_ko"] == one["line_ko"]) & (ms["station_ko"] == one["station_ko"])], b0, b1, full=True)["avg"]
base_v = base_one.get(key)
t = st.columns(4)
t[0].markdown(tile("Boardings a weekday", f"{cur / 1e3:.1f}k" if cur else "n/a", "latest 12 months"), unsafe_allow_html=True)
if cur and base_v:
    d = (cur / base_v - 1) * 100
    t[1].markdown(tile(f"vs {S.BASELINE_YEAR}", f"{d:+.0f}%", f"{base_v / 1e3:.1f}k a weekday in {S.BASELINE_YEAR}", d, ""), unsafe_allow_html=True)
else:
    t[1].markdown(tile(f"vs {S.BASELINE_YEAR}", "n/a", f"no full year of data in {S.BASELINE_YEAR}"), unsafe_allow_html=True)
t[2].markdown(tile("Rank on its line", f"{rank} of {len(line_now)}" if rank else "n/a", line_en.get(one["line_ko"], one["line_ko"])), unsafe_allow_html=True)
t[3].markdown(tile("Data from", pd.Timestamp(one["first_day"]).strftime("%b %Y"), "first month in the card data" if pd.Timestamp(one["first_day"]) > first_data + pd.DateOffset(days=31) else "station older than the data"), unsafe_allow_html=True)
fig = go.Figure()
fig.add_vrect(x0=S.COVID_START, x1=S.COVID_END, fillcolor=C["border"], opacity=0.45, line_width=0, annotation_text="COVID-19 rules", annotation_position="top left", annotation_font_color=C["muted"])
fig.add_scatter(x=hist["month"], y=hist["avg_all_days"] / 1e3, mode="lines", line=dict(color=C["muted"], width=1, dash="dot"), name="All days", hovertemplate="%{x|%b %Y}: %{y:.1f}k (all days)<extra></extra>")
fig.add_scatter(x=hist["month"], y=hist["avg_weekday"] / 1e3, mode="lines", line=dict(color=C["accent"], width=2.5), name="Weekdays", hovertemplate="%{x|%b %Y}: %{y:.1f}k (weekdays)<extra></extra>")
style(fig, 320)
fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.08, x=1, xanchor="right", font=dict(color=C["muted"])))
fig.update_yaxes(title_text="thousand boardings a day", title_font=dict(color=C["muted"], size=12), rangemode="tozero")
st.plotly_chart(fig, config=CHART_CONFIG, width="stretch")
st.markdown('<p class="note">Source: Seoul Open Data Plaza, daily card ridership by line and station. Weekday means Monday to Friday without public holidays. Station names: official English names where published, otherwise automatic romanisation.</p>', unsafe_allow_html=True)
