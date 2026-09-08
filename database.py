import sqlite3


DB_FILE = "pickem.db"


def create_database():

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            season INTEGER NOT NULL,
            week INTEGER NOT NULL,

            event_id TEXT NOT NULL UNIQUE,

            away_team TEXT NOT NULL,
            home_team TEXT NOT NULL,

            away_spread REAL,
            home_spread REAL,

            away_public_pct REAL,
            home_public_pct REAL,

            away_score REAL,
            home_score REAL,

            public_team TEXT,
            public_pct REAL,

            ats_winner TEXT,
            public_result TEXT
        )
    """)


    conn.commit()
    conn.close()


    print("Database ready:", DB_FILE)


if __name__ == "__main__":

    create_database()