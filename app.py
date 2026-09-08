import sqlite3
import pandas as pd
import streamlit as st


DB_FILE = "pickem.db"


# ---------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------

st.set_page_config(
    page_title="CFB Pick'em Analyzer",
    page_icon="🏈",
    layout="wide"
)


st.title("🏈 College Football Pick'em Analyzer")

st.caption(
    "ESPN public pick performance against the spread"
)


# ---------------------------------------------------------
# LOAD DATABASE
# ---------------------------------------------------------

@st.cache_data
def load_data():

    conn = sqlite3.connect(DB_FILE)

    query = """
        SELECT *
        FROM games
        ORDER BY season, week, event_id
    """

    df = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    return df


df = load_data()


if df.empty:

    st.warning(
        "No games found in the database."
    )

    st.stop()


# ---------------------------------------------------------
# DERIVED FIELDS
# ---------------------------------------------------------

def determine_favorite(row):

    if row["home_spread"] < 0:
        return row["home_team"]

    elif row["away_spread"] < 0:
        return row["away_team"]

    return "PICK"


def determine_underdog(row):

    if row["home_spread"] > 0:
        return row["home_team"]

    elif row["away_spread"] > 0:
        return row["away_team"]

    return "PICK"


def determine_public_side(row):

    if row["public_team"] == row["favorite_team"]:
        return "Favorite"

    elif row["public_team"] == row["underdog_team"]:
        return "Underdog"

    return "Pick'em"


def determine_public_location(row):

    if row["public_team"] == row["home_team"]:
        return "Home"

    elif row["public_team"] == row["away_team"]:
        return "Away"

    return "Unknown"


def determine_public_spread(row):

    if row["public_team"] == row["home_team"]:
        return row["home_spread"]

    elif row["public_team"] == row["away_team"]:
        return row["away_spread"]

    return None


df["favorite_team"] = df.apply(
    determine_favorite,
    axis=1
)

df["underdog_team"] = df.apply(
    determine_underdog,
    axis=1
)

df["public_side"] = df.apply(
    determine_public_side,
    axis=1
)

df["public_location"] = df.apply(
    determine_public_location,
    axis=1
)

df["public_spread"] = df.apply(
    determine_public_spread,
    axis=1
)


# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------

st.sidebar.header("Filters")


season_options = sorted(
    df["season"].dropna().unique()
)

selected_season = st.sidebar.selectbox(
    "Season",
    season_options,
    index=len(season_options) - 1
)


season_df = df[
    df["season"] == selected_season
].copy()


week_options = sorted(
    season_df["week"].dropna().unique()
)

selected_weeks = st.sidebar.multiselect(
    "Week",
    week_options,
    default=week_options
)


public_range = st.sidebar.slider(
    "Public Pick %",
    min_value=50,
    max_value=100,
    value=(50, 100)
)


selected_side = st.sidebar.selectbox(
    "Public Side",
    [
        "All",
        "Favorite",
        "Underdog"
    ]
)


selected_location = st.sidebar.selectbox(
    "Public Team Location",
    [
        "All",
        "Home",
        "Away"
    ]
)


spread_range = st.sidebar.slider(
    "Public Team Spread",
    min_value=-50.0,
    max_value=50.0,
    value=(-50.0, 50.0),
    step=0.5
)


# ---------------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------------

filtered = season_df.copy()


if selected_weeks:

    filtered = filtered[
        filtered["week"].isin(
            selected_weeks
        )
    ]


filtered = filtered[
    filtered["public_pct"].between(
        public_range[0],
        public_range[1]
    )
]


filtered = filtered[
    filtered["public_spread"].between(
        spread_range[0],
        spread_range[1]
    )
]


if selected_side != "All":

    filtered = filtered[
        filtered["public_side"]
        == selected_side
    ]


if selected_location != "All":

    filtered = filtered[
        filtered["public_location"]
        == selected_location
    ]


# Only graded games for ATS statistics
graded = filtered[
    filtered["public_result"].isin(
        ["WIN", "LOSS"]
    )
].copy()


# ---------------------------------------------------------
# SUMMARY METRICS
# ---------------------------------------------------------

wins = (
    graded["public_result"]
    == "WIN"
).sum()


losses = (
    graded["public_result"]
    == "LOSS"
).sum()


total_games = len(graded)


if total_games > 0:

    ats_pct = (
        wins
        / total_games
        * 100
    )

else:

    ats_pct = 0


st.subheader("Filtered Results")


col1, col2, col3, col4 = st.columns(4)


col1.metric(
    "Games",
    total_games
)


col2.metric(
    "ATS Record",
    f"{wins}-{losses}"
)


col3.metric(
    "ATS Win %",
    f"{ats_pct:.1f}%"
)


if total_games > 0:

    avg_public = graded[
        "public_pct"
    ].mean()

else:

    avg_public = 0


col4.metric(
    "Average Public Pick",
    f"{avg_public:.1f}%"
)


# ---------------------------------------------------------
# PUBLIC PERCENTAGE RANGE SUMMARY
# ---------------------------------------------------------

st.divider()

st.subheader(
    "Public Pick Performance by Percentage"
)


analysis_df = season_df[
    season_df["public_result"].isin(
        ["WIN", "LOSS"]
    )
].copy()


bins = [
    50,
    60,
    70,
    80,
    90,
    101
]


labels = [
    "50-59%",
    "60-69%",
    "70-79%",
    "80-89%",
    "90%+"
]


analysis_df["public_range"] = pd.cut(
    analysis_df["public_pct"],
    bins=bins,
    labels=labels,
    right=False
)


summary = (
    analysis_df
    .groupby(
        "public_range",
        observed=False
    )
    .agg(
        games=(
            "public_result",
            "count"
        ),

        wins=(
            "public_result",
            lambda x:
            (x == "WIN").sum()
        ),

        losses=(
            "public_result",
            lambda x:
            (x == "LOSS").sum()
        )
    )
    .reset_index()
)


summary["ATS %"] = (
    summary["wins"]
    / summary["games"]
    * 100
).round(1)


summary["Record"] = (
    summary["wins"].astype(str)
    + "-"
    + summary["losses"].astype(str)
)


summary_display = summary[
    [
        "public_range",
        "games",
        "Record",
        "ATS %"
    ]
].copy()


summary_display.columns = [
    "Public Pick %",
    "Games",
    "Record",
    "ATS %"
]


st.dataframe(
    summary_display,
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# FILTERED GAME DETAILS
# ---------------------------------------------------------

st.divider()

st.subheader(
    "Matching Games"
)


display_columns = [

    "week",

    "away_team",
    "home_team",

    "away_spread",
    "home_spread",

    "away_public_pct",
    "home_public_pct",

    "public_team",
    "public_pct",

    "public_side",
    "public_location",
    "public_spread",

    "away_score",
    "home_score",

    "ats_winner",
    "public_result"
]


game_display = filtered[
    display_columns
].copy()


game_display.columns = [

    "Week",

    "Away",
    "Home",

    "Away Spread",
    "Home Spread",

    "Away Public %",
    "Home Public %",

    "Public Team",
    "Public %",

    "Public Side",
    "Home/Away",
    "Public Spread",

    "Away Score",
    "Home Score",

    "ATS Winner",
    "Public Result"
]


st.dataframe(
    game_display,
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# RAW DATABASE INFO
# ---------------------------------------------------------

with st.expander(
    "Database Information"
):

    st.write(
        f"Total games stored: {len(df)}"
    )

    st.write(
        f"Database: {DB_FILE}"
    )

    st.write(
        f"Seasons stored: "
        f"{', '.join(map(str, season_options))}"
    )