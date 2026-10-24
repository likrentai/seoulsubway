"""Settings for the dashboard. Lines marked # <- are the ones you may want to change.
Colours of the page itself are in .streamlit/config.toml; the extra colours used for meaning are here."""

from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "app"   # <- folder with the summary files from 02dashdata

# Texts
APP_TITLE = "Seoul subway performance"                           # <- title at the top of every page
APP_SUBTITLE = "Daily ridership, crowding and service of the Seoul metropolitan subway, from real open data"   # <-
DATA_BADGE = "Real open data"                                    # <- small badge next to the title

# Comparison rules
BASELINE_YEAR = 2019                                             # <- pre-COVID year for the recovery index
COVID_START = "2020-02-01"                                       # <- shaded period in the trend chart
COVID_END = "2022-04-30"                                         # <- end of social-distancing rules in Korea
MIN_BASE_GROWTH = 5000                                           # <- fastest-growing station: weekday boardings a year earlier must be at least this
MIN_WEEKDAYS = 10                                                # <- a station month counts only with at least this many weekdays of data
PEOPLE_AT_100_PCT = 160                                          # <- crowding: 100% is about this many people in one car
N_ROUTES = 10                                                    # <- routes shown in the route chart

# VISUAL: colours that carry meaning (the page colours are in .streamlit/config.toml)
COLOR_GOOD = "#34D399"                                           # <- mint: recovery, growth
COLOR_WARN = "#F5B544"                                           # <- amber: busy
COLOR_BAD = "#F2685A"                                            # <- coral: very crowded, decline
COLOR_MUTED = "#8DA2C0"                                          # <- muted text and secondary lines
CROWD_BUSY = 35                                                  # <- crowding % from which a half hour shows amber
CROWD_VERY = 50                                                  # <- crowding % from which a half hour shows coral (network average)
GAUGE_RECOVERY_MAX = 120                                         # <- recovery meter scale, in %
GAUGE_CROWD_MAX = 200                                            # <- crowding meter scale, in %

# Page 2: ridership trends
TREND_DEFAULT_VIEW = "Monthly"                                   # <- first view shown: "Daily", "Weekly" or "Monthly"
CALENDAR_DEFAULT_YEAR = None                                     # <- year shown first in the calendar (None = latest full year)
YOY_WINDOW_MONTHS = 12                                           # <- route comparison: length of the recent period, in months

# Page 3: stations
TOP_N_DEFAULT = 15                                               # <- stations in the ranking at first
MIN_BASE_CHANGE = 5000                                           # <- gainers and losers: weekday boardings in the earlier period must be at least this
N_GAINERS = 10                                                   # <- gainers and losers shown
DEFAULT_STATION = "강남"                                          # <- station shown first in the station detail (Korean base name)
SEPARATE_NAMES = ["양평", "신촌"]                                   # <- names shared by two different stations (kept apart when lines are combined)

# Page 4: time of day (Seoul Metro hourly data, 2024)
AM_PEAK_HOURS = [7, 8]                                           # <- morning peak: hours starting 07:00 and 08:00
PM_PEAK_HOURS = [18, 19]                                         # <- evening peak: hours starting 18:00 and 19:00
HOME_SHARE = 0.65                                                # <- "home" station: at least this share of morning taps are boardings
WORK_SHARE = 0.35                                                # <- "work" station: at most this share of morning taps are boardings
MIN_MORNING_TAPS = 3000                                          # <- station character lists: at least this many morning-peak taps a weekday
DEFAULT_PROFILE_STATION = "강남"                                  # <- station shown first in the hourly profile (Korean base name)
COLOR_HOME = "#A78BFA"                                           # <- violet: home stations
COLOR_WORK = "#F5B544"                                           # <- amber: work stations

# Page 5: crowding (Seoul Metro Lines 1 to 8)
DIRECTION_NAMES = {                                              # <- plain-language names for the directions of each line
    "1호선": {"up": "towards Cheongnyangni", "down": "towards Seoul Station"},
    "2호선": {"inner": "inner loop (clockwise)", "outer": "outer loop (anticlockwise)"},
    "3호선": {"up": "towards Jichuk", "down": "towards Ogeum"},
    "4호선": {"up": "towards Buramsan", "down": "towards Namtaeryeong"},
    "5호선": {"up": "towards Banghwa", "down": "towards Hanam and Macheon"},
    "6호선": {"up": "towards Eungam", "down": "towards Sinnae"},
    "7호선": {"up": "towards Jangam", "down": "towards Onsu"},
    "8호선": {"up": "towards Amsa", "down": "towards Moran"},
}
DEFAULT_CROWD_LINE = "4호선"                                      # <- line shown first in the heatmap
CROWD_FULL = 100                                                 # <- crowding % counted as "full" in the tiles (100% is about 160 people per car)
N_TOP_CROWDED = 10                                               # <- rows in the most crowded list

# Page 6: service (Seoul Metro operations, March 2024)
SERVICE_YEAR = 2024                                              # <- year of ridership and crowding compared with the operations table
PEAK_HOUR = 8                                                    # <- peak hour for "people boarding per train" (8 means 08:00 to 09:00)
ROUTE_EN = {                                                     # <- English names of the routes in the operations table
    "1호선": "Seoul Station to Cheongnyangni",
    "2호선": "Circle line, plus Seongsu and Sinjeong branches",
    "3호선": "Jichuk to Ogeum",
    "4호선": "Jinjeop to Namtaeryeong",
    "5호선": "Banghwa to Hanam Geomdansan and Macheon",
    "6호선": "Eungam loop to Sinnae",
    "7호선": "Jangam to Onsu",
    "8호선": "Amsa to Moran",
}

# Page 7: about the data
AUTHOR = "Lik Ren Tai"                                  # <- shown in the credits
AUTHOR_NOTE = "Built as a hands-on data analytics portfolio project."
REPO_URL = ""                                                    # <- GitHub repository link (leave empty until it exists)
CASE_STUDY_URL = ""                                              # <- case study link (leave empty until it exists)
