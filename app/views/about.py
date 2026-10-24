"""Page 7: about the data. Sources, how the dashboard was made, definitions and the data issues that were found and handled."""

import pandas as pd
import streamlit as st

from app import settings as S
from app.data import load
from app.theme import colors, css, tile

css()
D = load()
C = colors()
days = D["daily_network"]
crowd_q = sorted(D["crowding_profile"]["quarter"].astype(str).unique())
q_label = lambda q: f"{q[:4]} Q{q[-1]}"

st.markdown(f'<h2 style="margin:0">About the data<span class="badge">{S.DATA_BADGE}</span></h2><p class="note" style="margin:0.2rem 0 0">Where the numbers come from, how they were prepared, and what to keep in mind when reading them.</p>', unsafe_allow_html=True)
st.markdown(f"""<style>
.about p, .about li {{font-size:0.95rem;line-height:1.6}}
.issue {{background:{C['panel']};border:1px solid {C['border']};border-left:3px solid {S.COLOR_WARN};border-radius:0 0.6rem 0.6rem 0;padding:0.6rem 0.9rem;margin:0 0 0.6rem}}
.issue b {{color:{C['text']}}}
.issue span {{color:{C['muted']};font-size:0.88rem}}
</style>""", unsafe_allow_html=True)

# ---------- 1. what this is ----------
t = st.columns(4)
t[0].markdown(tile("Daily ridership", f"{days['date'].min():%b %Y} to {days['date'].max():%b %Y}", f"{len(days):,} days, every line in the card data", small=True), unsafe_allow_html=True)
t[1].markdown(tile("Hourly gate counts", "2024", "Seoul Metro Lines 1 to 8, April left out", small=True), unsafe_allow_html=True)
t[2].markdown(tile("Crowding", f"{q_label(crowd_q[0])} to {q_label(crowd_q[-1])}", f"{len(crowd_q)} quarters, Seoul Metro Lines 1 to 8", small=True), unsafe_allow_html=True)
t[3].markdown(tile("Stations in the data", f"{len(D['stations']):,}", "one per line and station name", small=True), unsafe_allow_html=True)
st.markdown('<div class="about"><p>This dashboard tracks how the Seoul metropolitan subway is used: how many people ride, where and when, how full the trains are, and how much service is run. Everything shown is <b>real open data</b> published by the Seoul Metropolitan Government and Seoul Metro, covering the lines of Seoul Metro, KORAIL and the other operators in the card data. Nothing is simulated. The figures were downloaded, checked, cleaned and summarised in Python notebooks, and the app reads only the small summary files they produce.</p></div>', unsafe_allow_html=True)

# ---------- 2. how it was made ----------
st.markdown('<p class="sec">How it was made</p>', unsafe_allow_html=True)
dot = f"""digraph {{
  rankdir=LR; bgcolor="transparent"; nodesep=0.35; ranksep=0.45;
  node [shape=box, style="rounded,filled", fillcolor="{C['panel']}", color="{C['border']}", fontcolor="{C['text']}", fontname="Helvetica", fontsize=11, margin="0.18,0.1"];
  edge [color="{C['accent']}", arrowsize=0.7];
  raw [label="Raw files\\nSeoul Open Data Plaza,\\ndata.go.kr, Open API"];
  check [label="00datacheck\\n00download\\ninspect and fetch"];
  clean [label="01clean\\ntidy tables\\n(2.5 M daily rows)"];
  dash [label="02dashdata\\nsmall summaries\\n(about 5 MB)"];
  app [label="Streamlit app\\nseven pages", fillcolor="{C['accent']}", fontcolor="{C['bg']}", color="{C['accent']}"];
  raw -> check -> clean -> dash -> app;
}}"""
st.graphviz_chart(dot, width="stretch")

# ---------- 3. sources ----------
st.markdown('<p class="sec">Sources</p>', unsafe_allow_html=True)
src = pd.DataFrame([
    ["Daily boardings and alightings by line and station (card data)", "Seoul City", f"{days['date'].min():%Y} to {days['date'].max():%b %Y}", "Overview, Trends, Stations, Service", "https://data.seoul.go.kr/dataList/OA-12914/S/1/datasetView.do"],
    ["Same data through the Open API, for the latest months", "Seoul City", "last 7 months", "Overview, Trends, Stations", "https://data.seoul.go.kr/dataList/OA-12914/S/1/datasetView.do"],
    ["Boardings and alightings by station and hour", "Seoul Metro", "2024", "Time of day, Service", "https://www.data.go.kr/data/15048032/fileData.do"],
    ["Crowding by station, direction and half hour", "Seoul Metro", f"{q_label(crowd_q[0])} to {q_label(crowd_q[-1])}", "Overview, Crowding, Service", "https://data.seoul.go.kr/dataList/OA-12928/S/1/datasetView.do"],
    ["Train operation status by line (length, headways, trips, fleet)", "Seoul Metro", "March 2024", "Service", "https://data.seoul.go.kr/dataList/OA-13318/S/1/datasetView.do"],
    ["Station names in several languages (official English names)", "Seoul Metro", "2026", "all pages", "https://www.data.go.kr/data/15044232/fileData.do"],
    ["Korean public holidays (Python package holidays)", "open source", "2015 to 2026", "all pages", "https://pypi.org/project/holidays/"],
], columns=["Dataset", "Publisher", "Coverage", "Used on", "Link"])
st.dataframe(src, hide_index=True, width="stretch", column_config={"Dataset": st.column_config.TextColumn(width="large"), "Publisher": st.column_config.TextColumn(width="small"), "Coverage": st.column_config.TextColumn(width="medium"), "Used on": st.column_config.TextColumn(width="medium"), "Link": st.column_config.LinkColumn("Link", display_text="open", width="small")})

# ---------- 4. definitions ----------
st.markdown('<p class="sec">Definitions</p>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
c1.markdown(f"""<div class="about"><ul>
<li><b>Boardings</b>: people entering a station through the gates, counted from transit cards (tap-ins).</li>
<li><b>Weekday</b>: Monday to Friday without public holidays. Holidays come from the Korean calendar, plus Workers' Day (1 May, before it became a public holiday in 2026) and two bridge days in 2025. The headline figures use the average weekday, because whole-month averages shift with the dates of Seollal and Chuseok.</li>
<li><b>Recovery</b>: average weekday boardings as a share of the same month in {S.BASELINE_YEAR}, the last year before COVID-19.</li>
<li><b>Like-for-like</b>: comparisons over time only use stations with data in every month of both periods, so new stations and stations that left the data do not show up as growth or decline.</li>
</ul></div>""", unsafe_allow_html=True)
c2.markdown(f"""<div class="about"><ul>
<li><b>Crowding %</b>: Seoul Metro's measure of how full trains are when they leave a station. 34% means every seat is taken; 100% means about {S.PEOPLE_AT_100_PCT} people in one car. Each value is the average over the trains in a half hour.</li>
<li><b>Line and route</b>: the card data splits long KORAIL routes into their historic sections (for example the Gyeongbu and Gyeongwon Lines). A <i>route</i> groups them into the coloured line passengers know, such as Line 1.</li>
<li><b>Station names</b>: Korean names are always shown. English names are the official Seoul Metro names where published, otherwise an automatic romanisation. Subtitles in brackets are dropped and renamed stations are joined into one history.</li>
<li><b>Transfer stations</b> count once per line, as in the card data, unless a page says the lines are combined.</li>
</ul></div>""", unsafe_allow_html=True)

# ---------- 5. issues ----------
st.markdown('<p class="sec">Data issues found and how they were handled</p>', unsafe_allow_html=True)
issues = [
    ("Hourly counts for April 2024 are wrong in the source file", "The 13:00 hour is about ten times too high on every day of April 2024. April is left out of the Time of day and Service pages; without it, the hourly totals match the daily card data to within 0.5%."),
    ("New lines take over taps at existing stations", "When a line opens at a station (for example Boramae, Gimpo Airport or Magoknaru), part of the station's passengers are booked to the new line, so the old line seems to lose riders. Station rankings of gainers and losers compare whole stations whose lines did not change."),
    ("Stations leave or join the data", "The Bucheon and Incheon section of Line 7 left the card data between 2022 and 2024, and extensions added stations to Lines 5 and 8. Like-for-like comparisons remove both effects (Line 7 changes from -17% to about -5% against 2019)."),
    ("Calendar effects", "Chuseok fell in September 2026 but in October 2025, so the all-days average for September looks lower than a year earlier while the weekday average is higher. Headline comparisons use weekdays."),
    ("A missing quarter and three layouts in the crowding files", "2024 Q3 was never published, so charts show a gap there. The other quarters come in three layouts (different line labels, half-hour labels, sheets and padded text), which are harmonised; a few rows with an old station name or wrong line are corrected from Seoul Metro's station codes."),
    ("Messy download files", "Yearly files mix encodings (CP949 and UTF-8), one file has two rows glued together, number formats change between years, and a few Gyeongui Line stations have small duplicate rows. All are repaired when reading."),
    ("The Open API only keeps recent months", "The API holds about the last seven months, so the history comes from the yearly and monthly files and the API is used to keep the latest months up to date. Where both exist, the downloaded file is used."),
    ("Weekdays with unusual ridership", "Days much quieter than the weekdays around them were checked by hand: Workers' Day and two 2025 bridge days are treated as holidays; 10 August 2023 (Typhoon Khanun) is a real disruption and stays a weekday."),
]
for head, body in issues:
    st.markdown(f'<div class="issue"><b>{head}</b><br><span>{body}</span></div>', unsafe_allow_html=True)

# ---------- 6. credits ----------
st.markdown('<p class="sec">Credits and licence</p>', unsafe_allow_html=True)
links = []
if S.REPO_URL:
    links.append(f'<a href="{S.REPO_URL}">notebooks and code on GitHub</a>')
if S.CASE_STUDY_URL:
    links.append(f'<a href="{S.CASE_STUDY_URL}">case study</a>')
link_text = f" See the {' and the '.join(links)}." if links else ""
st.markdown(f'<div class="about"><p>Dashboard by <b>{S.AUTHOR}</b>. {S.AUTHOR_NOTE}{link_text}</p><p class="note">Data: Seoul Metropolitan Government and Seoul Metro, published as open data on Seoul Open Data Plaza and the Korean Public Data Portal (data.go.kr), free to use with credit to the source. This dashboard is an independent project and is not affiliated with or endorsed by any of these organisations. Built with Python (pandas, Plotly, Streamlit).</p></div>', unsafe_allow_html=True)
