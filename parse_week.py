import json
import pandas as pd
import sqlite3


INPUT_FILE = "espn_week1_raw.json"


# ---------------------------------------------------------
# Load ESPN JSON
# ---------------------------------------------------------

with open(INPUT_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)


games = []


# ---------------------------------------------------------
# Loop through ESPN propositions
# ---------------------------------------------------------

for prop in data.get("propositions", []):

    # We only care about propositions that have a spread.
    if "spread" not in prop:
        continue

    outcomes = prop.get("possibleOutcomes", [])

    if len(outcomes) != 2:
        continue


    away = None
    home = None

    for outcome in outcomes:

        if outcome.get("subType") == "AWAY":
            away = outcome

        elif outcome.get("subType") == "HOME":
            home = outcome


    if not away or not home:
        continue


    # -----------------------------------------------------
    # ESPN represents the spread from the HOME perspective
    #
    # Example:
    # Ohio @ Nebraska
    # spread = -23.5
    #
    # Nebraska = -23.5
    # Ohio     = +23.5
    # -----------------------------------------------------

    home_spread = float(prop["spread"])
    away_spread = -home_spread


    # -----------------------------------------------------
    # Find ESPN public pick percentage for ATS
    #
    # scoringFormatId 3 = SPREAD / ATS for these games
    # -----------------------------------------------------

    def get_spread_percentage(team):

        for counter in team.get("choiceCounters", []):

            if counter.get("scoringFormatId") == 3:

                return (
                    counter.get("percentage", 0)
                    * 100
                )

        return None


    away_pct = get_spread_percentage(away)
    home_pct = get_spread_percentage(home)


    # -----------------------------------------------------
    # Determine ESPN event ID
    # -----------------------------------------------------

    event_id = None

    for mapping in prop.get("mappings", []):

        if mapping.get("type") == "EVENT_ID":
            event_id = mapping.get("value")
            break


    # -----------------------------------------------------
    # Scores
    # -----------------------------------------------------

    away_score = away.get("score")
    home_score = home.get("score")


    # -----------------------------------------------------
    # Determine ATS result ourselves
    #
    # Adjusted score:
    #
    # Nebraska 49 + (-23.5) = 25.5
    # Ohio     21
    #
    # 25.5 > 21
    # Nebraska covers
    # -----------------------------------------------------

    ats_winner = None

    if (
        away_score is not None
        and home_score is not None
    ):

        home_adjusted = home_score + home_spread
        away_adjusted = away_score + away_spread

        if home_adjusted > away_score:
            ats_winner = home["name"]

        elif away_adjusted > home_score:
            ats_winner = away["name"]

        else:
            ats_winner = "PUSH"


    # -----------------------------------------------------
    # Identify public favorite
    # -----------------------------------------------------

    public_team = None
    public_pct = None

    if away_pct is not None and home_pct is not None:

        if away_pct > home_pct:
            public_team = away["name"]
            public_pct = away_pct

        else:
            public_team = home["name"]
            public_pct = home_pct


    # Did the public side cover?
    public_result = None

    if public_team and ats_winner:

        if ats_winner == "PUSH":
            public_result = "PUSH"

        elif public_team == ats_winner:
            public_result = "WIN"

        else:
            public_result = "LOSS"


    # -----------------------------------------------------
    # Save row
    # -----------------------------------------------------

    games.append({

        "week":
            prop.get("scoringPeriodId"),

        "event_id":
            event_id,

        "away_team":
            away["name"],

        "home_team":
            home["name"],

        "away_spread":
            away_spread,

        "home_spread":
            home_spread,

        "away_public_pct":
            round(away_pct, 1)
            if away_pct is not None
            else None,

        "home_public_pct":
            round(home_pct, 1)
            if home_pct is not None
            else None,

        "away_score":
            away_score,

        "home_score":
            home_score,

        "public_team":
            public_team,

        "public_pct":
            round(public_pct, 1)
            if public_pct is not None
            else None,

        "ats_winner":
            ats_winner,

        "public_result":
            public_result

    })


# ---------------------------------------------------------
# Convert to table
# ---------------------------------------------------------

df = pd.DataFrame(games)


# Sort by game
df = df.sort_values(
    by=["week", "event_id"]
)


# ---------------------------------------------------------
# Show results
# ---------------------------------------------------------

pd.set_option(
    "display.max_columns",
    None
)

pd.set_option(
    "display.width",
    200
)


print()
print("=" * 100)
print("ESPN COLLEGE PICK'EM - WEEK DATA")
print("=" * 100)
print()

print(df.to_string(index=False))

print()


# ---------------------------------------------------------
# Save CSV
# ---------------------------------------------------------

OUTPUT_FILE = "week1_parsed.csv"

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print(
    f"Saved {len(df)} games to {OUTPUT_FILE}"
)
# ---------------------------------------------------------
# Save to SQLite database
# ---------------------------------------------------------

DB_FILE = "pickem.db"

conn = sqlite3.connect(DB_FILE)

cursor = conn.cursor()


for _, row in df.iterrows():

    cursor.execute(
        """
        INSERT INTO games (

            season,
            week,
            event_id,

            away_team,
            home_team,

            away_spread,
            home_spread,

            away_public_pct,
            home_public_pct,

            away_score,
            home_score,

            public_team,
            public_pct,

            ats_winner,
            public_result

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(event_id)
        DO UPDATE SET

            week = excluded.week,

            away_team = excluded.away_team,
            home_team = excluded.home_team,

            away_spread = excluded.away_spread,
            home_spread = excluded.home_spread,

            away_public_pct = excluded.away_public_pct,
            home_public_pct = excluded.home_public_pct,

            away_score = excluded.away_score,
            home_score = excluded.home_score,

            public_team = excluded.public_team,
            public_pct = excluded.public_pct,

            ats_winner = excluded.ats_winner,
            public_result = excluded.public_result
        """,

        (
            2026,
            row["week"],
            row["event_id"],

            row["away_team"],
            row["home_team"],

            row["away_spread"],
            row["home_spread"],

            row["away_public_pct"],
            row["home_public_pct"],

            row["away_score"],
            row["home_score"],

            row["public_team"],
            row["public_pct"],

            row["ats_winner"],
            row["public_result"]
        )
    )


conn.commit()
conn.close()


print(
    f"Saved {len(df)} games to {DB_FILE}"
)