"""
Sports Betting Model - Data Processing Module

This module contains functions to interact with the Sports Game Odds API,
retrieve betting odds, and process the data for analysis.
"""

import requests
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta, timezone
import time
import os
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debug prints to check environment variables
# print("Current working directory:", os.getcwd())
# print("Environment variables loaded:")
# print("SPORTSGAMEODDS_API_KEY:", os.environ.get("SPORTSGAMEODDS_API_KEY"))
# print("SPORTSGAMEODDS_BASE_URL:", os.environ.get("SPORTSGAMEODDS_BASE_URL"))

# Get environment variables with defaults for local development
API_KEY = os.environ.get("SPORTSGAMEODDS_API_KEY", "54d3becdef2171632a399753a3a85f5d")
BASE_URL = os.environ.get("SPORTSGAMEODDS_BASE_URL", "https://api.sportsgameodds.com/v2")
HEADERS = {
    "X-Api-Key": API_KEY
}

# Define supported leagues
# LEAGUES = ["NBA", "WNBA", "MLB", "NHL"]
LEAGUES = ["NBA"]

def make_api_request(endpoint: str, params: Dict = None) -> Dict:
    url = f"{BASE_URL}/{endpoint}"
    print(f"API Request: {endpoint} - {params.get('eventID', '') if params else ''}")
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        time.sleep(1)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return {"success": False, "error": str(e)}

def get_upcoming_games(league: str = "NBA") -> pd.DataFrame:
    # Current time in UTC
    current_time_utc = datetime.now(timezone.utc)
    
    # Add 24 hours
    end_time_utc_24 = current_time_utc + timedelta(hours=24)
    
    # Format to ISO 8601 (with Z for UTC)
    starts_after = current_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    starts_before_24 = end_time_utc_24.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    print("START TIME (UTC):", starts_after)
    print("END TIME (UTC):", starts_before_24)

    params = {
        "leagueID": league,
        "startsAfter": starts_after,
        "startsBefore": starts_before_24,
        "limit": 100
    }

    print(f"\n📅 Fetching upcoming {league} games (next 24 hours)...")
    response = make_api_request("events", params)

    if response.get("success"):
        events_data = response.get("data", [])
        if events_data:
            print(f"✅ Found {len(events_data)} upcoming {league} games")
            processed_events = []
            for event in events_data:
                event_id = event.get("eventID", "")
                teams = event.get("teams", {})
                home_team = teams.get("home", {})
                away_team = teams.get("away", {})

                hours_offset = len(processed_events) % 24
                placeholder_time = current_time_utc + timedelta(hours=hours_offset)
                start_time = placeholder_time.strftime("%Y-%m-%dT%H:%M:%SZ")

                processed_event = {
                    "eventID": event_id,
                    "startTime": start_time,
                    "homeTeam": home_team,
                    "awayTeam": away_team,
                    "league": league,
                    "rawData": event
                }

                processed_events.append(processed_event)

            return pd.DataFrame(processed_events)
        else:
            print(f"❌ No upcoming {league} games found in the next 24 hours")
            return pd.DataFrame()
    else:
        print(f"❌ Error fetching {league} events: {response.get('error')}")
        return pd.DataFrame()

def get_player_props(event_id: str, home_team: str, away_team: str, league: str) -> pd.DataFrame:
    params = {
        "eventID": event_id
    }

    print(f"🏀 Fetching player props for {away_team} @ {home_team} (event ID: {event_id})")
    response = make_api_request("events", params)

    if response.get("success"):
        events_data = response.get("data", [])
        if not events_data:
            print("❌ No event data found")
            return pd.DataFrame()

        event = events_data[0]
        odds_dict = event.get("odds", {})
        player_props = []

        league_suffix = f"_{league}"
        for odd_id, odd_data in odds_dict.items():
            if "PLAYER" in odd_id or league_suffix in odd_id:
                parts = odd_id.split("-")
                if len(parts) >= 3:
                    prop_type = parts[0]
                    player_id = parts[1] if len(parts) > 1 else ""
                    direction = parts[-1] if len(parts) > 2 else ""

                    prop = {
                        "oddID": odd_id,
                        "prop_type": prop_type,
                        "player_id": player_id,
                        "direction": direction,
                        "eventID": event_id,
                        "league": league
                    }

                    if odd_data:
                        for key, value in odd_data.items():
                            prop[key] = value

                    player_props.append(prop)

        print(f"✅ Found {len(player_props)} player props")
        return pd.DataFrame(player_props)
    else:
        print(f"❌ Error fetching event: {response.get('error')}")
        return pd.DataFrame()

def parse_player_id(player_id: str, league: str) -> str:
    if not player_id or not isinstance(player_id, str):
        return "Unknown"

    name_parts = player_id.split("_")
    league_suffix = league
    if len(name_parts) >= 3 and name_parts[-1] == league_suffix:
        name_parts = name_parts[:-2]

    name = " ".join(name_parts).title()
    return name

def process_player_props(props_df: pd.DataFrame) -> pd.DataFrame:
    if props_df.empty:
        return pd.DataFrame()

    processed_df = props_df.copy()
    if "player_id" in processed_df.columns and "league" in processed_df.columns:
        processed_df["player_name"] = processed_df.apply(
            lambda row: parse_player_id(row["player_id"], row["league"]), axis=1
        )

    if "oddID" in processed_df.columns and "prop_type" not in processed_df.columns:
        processed_df["prop_details"] = processed_df["oddID"].apply(lambda x: x.split("-"))
        processed_df["prop_type"] = processed_df["prop_details"].apply(lambda x: x[0] if len(x) > 0 else "Unknown")
        processed_df["player_id"] = processed_df["prop_details"].apply(lambda x: x[1] if len(x) > 1 else "Unknown")
        processed_df["direction"] = processed_df["prop_details"].apply(lambda x: x[-1] if len(x) > 2 else "Unknown")
        
        if "league" in processed_df.columns:
            processed_df["player_name"] = processed_df.apply(
                lambda row: parse_player_id(row["player_id"], row["league"]), axis=1
            )
        
        processed_df.drop("prop_details", axis=1, inplace=True)

    if "americanOdds" in processed_df.columns:
        processed_df["decimal_odds"] = processed_df["americanOdds"].apply(
            lambda x: convert_american_to_decimal(x) if pd.notnull(x) else None
        )
        processed_df["implied_probability"] = processed_df["decimal_odds"].apply(
            lambda x: calculate_implied_probability(x) if pd.notnull(x) else None
        )

    return processed_df

def convert_american_to_decimal(american_odds):
    if pd.isnull(american_odds):
        return None

    american_odds = float(american_odds)
    if american_odds > 0:
        return round((american_odds / 100) + 1, 4)
    else:
        return round((100 / abs(american_odds)) + 1, 4)

def calculate_implied_probability(decimal_odds):
    if pd.isnull(decimal_odds) or decimal_odds == 0:
        return None

    return round(1 / float(decimal_odds), 4)

def extract_team_name(team_data: Dict, league: str) -> str:
    if not team_data:
        return "Unknown"

    names = team_data.get("names", {})
    if names:
        return (
            names.get("medium") or
            names.get("long") or
            names.get("short") or
            "Unknown"
        )

    team_id = team_data.get("teamID", "")
    if team_id:
        parts = team_id.split("_")
        league_suffix = league
        if len(parts) >= 2 and parts[-1] == league_suffix:
            parts = parts[:-1]
            return " ".join(parts).title()

    return "Unknown"

def main():
    all_games_df = pd.DataFrame()
    
    # Get games for each league
    for league in LEAGUES:
        games_df = get_upcoming_games(league)
        if not games_df.empty:
            all_games_df = pd.concat([all_games_df, games_df], ignore_index=True)
    
    if all_games_df.empty:
        print("❌ No upcoming games found for any league")
        return

    print("\n📋 Upcoming Games (Note: Times are placeholders):")
    for _, game in all_games_df.iterrows():
        try:
            game_time_utc = datetime.strptime(game['startTime'], "%Y-%m-%dT%H:%M:%SZ")
            game_time_est = game_time_utc.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=-5)))
            league = game['league']
            home_team = extract_team_name(game['homeTeam'], league)
            away_team = extract_team_name(game['awayTeam'], league)
            print(f"  • [{league}] {game_time_est.strftime('%Y-%m-%d %I:%M %p EST')}: {away_team} @ {home_team} (ID: {game['eventID']})")
        except Exception as e:
            print(f"❌ Error displaying game: {e}")

    print("\n🔍 Collecting player props for all games...")
    all_props = []

    # EXCEPT FOR THESE GAME IDs
    EXCEPT_EVENT_IDs = ['ppwvEzsFQ6V1tS0oONvs']

    for _, game in all_games_df.iterrows():
        try:
            event_id = game['eventID']
            league = game['league']
            home_team = extract_team_name(game['homeTeam'], league)
            away_team = extract_team_name(game['awayTeam'], league)
            if event_id not in EXCEPT_EVENT_IDs:
                print(f"\n📊 Processing {league} game: {away_team} @ {home_team} (ID: {event_id})")
                props_df = get_player_props(event_id, home_team, away_team, league)

                if props_df.empty:
                    print(f"❌ No player props found for {away_team} @ {home_team}")
                    continue

                processed_props = process_player_props(props_df)
                if not processed_props.empty:
                    processed_props['home_team'] = home_team
                    processed_props['away_team'] = away_team
                    processed_props['game'] = f"{away_team} @ {home_team}"
                    processed_props['game_number'] = event_id
                    processed_props['event_id'] = event_id
                    processed_props['league'] = league

                    all_props.append(processed_props)

                    player_counts = processed_props['player_name'].value_counts()
                    most_common_players = player_counts.nlargest(5)
                    print(f"  • Found props for {len(player_counts)} players")
                    print(f"  • Top players: {', '.join([f'{player} ({count})' for player, count in most_common_players.items()])}")
                else:
                    print("❌ Failed to process player props")
        except Exception as e:
            print(f"❌ Error processing game {event_id}: {e}")

    if all_props:
        combined_props = pd.concat(all_props, ignore_index=True)
        timestamp = datetime.now().strftime('%Y-%m-%d')
        
        # Save all combined props
        all_output_file = f"basketball_player_props_{timestamp}.csv"
        combined_props.to_csv(all_output_file, index=False)
        print(f"\n✅ Saved {len(combined_props)} total player props to {all_output_file}")
        
        # Also save separate files for each league
        for league in LEAGUES:
            league_props = combined_props[combined_props['league'] == league]
            if not league_props.empty:
                league_output_file = f"{league.lower()}_player_props_{timestamp}.csv"
                league_props.to_csv(league_output_file, index=False)
                print(f"✅ Saved {len(league_props)} {league} player props to {league_output_file}")
    else:
        print("\n❌ No player props found for any games")

if __name__ == "__main__":
    main()
