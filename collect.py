import json
import sqlite3
from datetime import datetime
from pathlib import Path

import requests


CHALLENGE = "college-football-pickem-2026"
DB_FILE = "pickem.db"

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def get_ats_percentage(team):
    for counter in team.get("choiceCounters", []):
        if counter.get("scoringFormatId") == 3:
            return counter.get("percentage", 0) * 100

    return None


def get_event_id(prop):
    for mapping in prop.get("mappings", []):
        if mapping.get("type") == "EVENT_ID":
            return mapping.get("value")

    return None


def fetch_espn():

    url = (
        "https://gambit-api.fantasy.espn.com/apis/v1/challenges/"
        f"{CHALLENGE}"
    )

    params = {
        "view": "chui_default"
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/152 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def save_raw_json(data, week):

    filename = RAW_DIR / f"week_{week}.json"

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2
        )

    print(f"Raw ESPN JSON saved to: {filename}")


def collect_games(data):

    games = []

    current_period = data.get("currentScoringPeriod", {})

    current_week = current_period.get("id")

    print()
    print("Current ESPN Week:", current_week)

    for prop in data.get("propositions", []):

        if prop.get("scoringPeriodId") != current_week:
            continue

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

        home_spread = float(prop["spread"])
        away_spread = -home_spread

        away_pct = get_ats_percentage(away)
        home_pct = get_ats_percentage(home)

        away_score = away.get("score")
        home_score = home.get("score")

        event_id = get_event_id(prop)

        ats_winner = None

        if (
            away_score is not None
            and home_score is not None
            and prop.get("status") == "COMPLETE"
        ):

            home_adjusted = home_score + home_spread
            away_adjusted = away_score + away_spread

            if home_adjusted > away_score:
                ats_winner = home["name"]

            elif away_adjusted > home_score:
                ats_winner = away["name"]

            else:
                ats_winner = "PUSH"

        public_team = None
        public_pct = None

        if away_pct is not None and home_pct is not None:

            if away_pct > home_pct:
                public_team = away["name"]
                public_pct = away_pct

            else:
                public_team = home["name"]
                public_pct = home_pct

        public_result = None

        if public_team and ats_winner:

            if ats_winner == "PUSH":
                public_result = "PUSH"

            elif public_team == ats_winner:
                public_result = "WIN"

            else:
                public_result = "LOSS"

        games.append(
            {
                "season": 2026,
                "week": current_week,
                "event_id": event_id,

                "away_team": away["name"],
                "home_team": home["name"],

                "away_spread": away_spread,
                "home_spread": home_spread,

                "away_public_pct": (
                    round(away_pct, 1)
                    if away_pct is not None
                    else None
                ),

                "home_public_pct": (
                    round(home_pct, 1)
                    if home_pct is not None
                    else None
                ),

                "away_score": away_score,
                "home_score": home_score,

                "public_team": public_team,

                "public_pct": (
                    round(public_pct, 1)
                    if public_pct is not None
                    else None
                ),

                "ats_winner": ats_winner,
                "public_result": public_result
            }
        )

    return current_week, games


def save_to_database(games):

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for game in games:

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

                season = excluded.season,
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
                game["season"],
                game["week"],
                game["event_id"],

                game["away_team"],
                game["home_team"],

                game["away_spread"],
                game["home_spread"],

                game["away_public_pct"],
                game["home_public_pct"],

                game["away_score"],
                game["home_score"],

                game["public_team"],
                game["public_pct"],

                game["ats_winner"],
                game["public_result"]
            )
        )

    conn.commit()
    conn.close()


def main():

    print()
    print("=" * 60)
    print("ESPN COLLEGE PICK'EM COLLECTOR")
    print("=" * 60)

    print()
    print("Downloading ESPN data...")

    data = fetch_espn()

    week, games = collect_games(data)

    save_raw_json(
        data,
        week
    )

    save_to_database(
        games
    )

    print()
    print(f"Games processed: {len(games)}")
    print(f"Database updated: {DB_FILE}")

    print()
    print("Complete.")
    print()


if __name__ == "__main__":
    main()