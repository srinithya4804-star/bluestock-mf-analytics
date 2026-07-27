"""
Bluestock Capstone Project I - Mutual Fund Analytics
Day 1 - Live NAV Fetch

Covers:
  Step 4 - Fetch live NAV for HDFC Top 100 Direct (125497) from mfapi.in
  Step 5 - Fetch NAV for 5 key schemes: SBI Bluechip, ICICI Bluechip,
           Nippon Large Cap, Axis Bluechip, Kotak Bluechip
"""

import os
import time
import requests
import pandas as pd

RAW_DIR = "data/raw"

# Step 5: 5 key schemes (name -> AMFI scheme code)
KEY_SCHEMES = {
    "SBI_Bluechip": 119551,
    "ICICI_Bluechip": 120503,
    "Nippon_Large_Cap": 118632,
    "Axis_Bluechip": 119092,
    "Kotak_Bluechip": 120841,
}

# Step 4: HDFC Top 100 Direct
PRIMARY_SCHEME = {"HDFC_Top_100_Direct": 125497}

BASE_URL = "https://api.mfapi.in/mf/{code}"


def fetch_scheme_nav(code: int) -> dict:
    """Call mfapi.in for a single scheme code and return the parsed JSON."""
    url = BASE_URL.format(code=code)
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


def save_nav_as_csv(scheme_name: str, code: int, payload: dict, raw_dir: str):
    """
    Parse the mfapi.in JSON response into a DataFrame and save as CSV.
    mfapi.in response shape:
      {
        "meta": {fund_house, scheme_type, scheme_category, scheme_code, scheme_name, ...},
        "data": [{"date": "dd-mm-yyyy", "nav": "123.4567"}, ...]
      }
    """
    meta = payload.get("meta", {})
    nav_records = payload.get("data", [])

    if not nav_records:
        print(f"  No NAV data returned for {scheme_name} ({code}) - skipping save.")
        return

    df = pd.DataFrame(nav_records)
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df["scheme_code"] = meta.get("scheme_code", code)
    df["scheme_name"] = meta.get("scheme_name", scheme_name)
    df["fund_house"] = meta.get("fund_house")
    df["scheme_category"] = meta.get("scheme_category")

    df = df.sort_values("date").reset_index(drop=True)

    os.makedirs(raw_dir, exist_ok=True)
    out_path = os.path.join(raw_dir, f"nav_{scheme_name}_{code}.csv")
    df.to_csv(out_path, index=False)

    print(f"  Saved {len(df)} NAV records for {scheme_name} ({code}) -> {out_path}")


def fetch_and_save(schemes: dict, raw_dir: str):
    for scheme_name, code in schemes.items():
        print(f"Fetching NAV for {scheme_name} (code {code}) ...")
        try:
            payload = fetch_scheme_nav(code)
            save_nav_as_csv(scheme_name, code, payload, raw_dir)
        except requests.exceptions.RequestException as e:
            print(f"  Failed to fetch {scheme_name} ({code}): {e}")
        time.sleep(1)  # be polite to the free API


def main():
    print("=" * 80)
    print("STEP 4: Fetch live NAV - HDFC Top 100 Direct")
    print("=" * 80)
    fetch_and_save(PRIMARY_SCHEME, RAW_DIR)

    print("\n" + "=" * 80)
    print("STEP 5: Fetch live NAV - 5 key schemes")
    print("=" * 80)
    fetch_and_save(KEY_SCHEMES, RAW_DIR)


if __name__ == "__main__":
    main()
