import requests
import json


CHALLENGE = "college-football-pickem-2026"
WEEK = 1


url = (
    f"https://gambit-api.fantasy.espn.com/apis/v1/challenges/"
    f"{CHALLENGE}"
)

params = {
    "scoringPeriodId": WEEK,
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


print("STATUS:", response.status_code)
print()
print("FINAL URL:")
print(response.url)
print()


if response.ok:

    data = response.json()

    print("TOP LEVEL JSON KEYS:")
    print(list(data.keys()) if isinstance(data, dict) else type(data))

    print()

    with open(
        "espn_week1_raw.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2
        )

    print("Saved:")
    print("espn_week1_raw.json")

else:

    print(response.text[:3000])