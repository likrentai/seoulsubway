"""Seoul subway KPI dashboard. Start with:  streamlit run streamlit_app.py"""

import streamlit as st

from app import settings as S

st.set_page_config(page_title=S.APP_TITLE, page_icon=":material/subway:", layout="wide")

pages = [
    st.Page("app/views/overview.py", title="Overview", icon=":material/dashboard:", default=True),
    st.Page("app/views/trends.py", title="Ridership trends", icon=":material/trending_up:"),
    st.Page("app/views/stations.py", title="Stations", icon=":material/location_on:"),
    st.Page("app/views/timeofday.py", title="Time of day", icon=":material/schedule:"),
    st.Page("app/views/crowding.py", title="Crowding", icon=":material/groups:"),
    st.Page("app/views/service.py", title="Service", icon=":material/train:"),
    st.Page("app/views/about.py", title="About the data", icon=":material/info:"),
]
st.navigation(pages).run()
