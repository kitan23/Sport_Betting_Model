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
from typing import Dict, List, Any, Optional, Union

API_KEY = "f368467e5c8ec70161ce40549e899406"
BASE_URL = "https://api.sportsgameodds.com/v2"
HEADERS = {
    "X-Api-Key": API_KEY
}

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

def get_upcoming_nba_games() -> pd.DataFrame:
    """
    Get upcoming NBA games in the next 24 hours.
    Handles timezone conversion between EST (local) and UTC (API).
    
    Returns:
        DataFrame containing upcoming NBA games
    """
    # Get current time in UTC (API timezone)
    current_time_utc = datetime.now(timezone.utc) - timedelta(hours=3)
    
    # Calculate hours from now in UTC
    end_time_utc_12 = current_time_utc + timedelta(hours=4)
    
    # Format times for API
    starts_after = current_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    starts_before_12 = end_time_utc_12.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Set up parameters for API request
    params = {
        "leagueID": "NBA",
        "startsAfter": starts_after,
        "startsBefore": starts_before_12,
        "limit": 100
    }
    
    print(f"\n📅 Fetching upcoming NBA games (next 24 hours)...")
    response = make_api_request("events", params)
    
    if response.get("success"):
        events_data = response.get("data", [])
        if events_data:
            print(f"✅ Found {len(events_data)} upcoming NBA games")
            
            # Process the events data to ensure it has the fields we need
            processed_events = []
            for event in events_data:
                # Extract the event ID
                event_id = event.get("eventID", "")
                
                # Extract team information
                teams = event.get("teams", {})
                home_team = teams.get("home", {})
                away_team = teams.get("away", {})
                
                # Since the API doesn't provide start time, use a placeholder
                # Generate a placeholder time between now and 24 hours from now
                hours_offset = len(processed_events) % 24  # Spread games across 24 hours
                placeholder_time = current_time_utc + timedelta(hours=hours_offset)
                start_time = placeholder_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                
                # Create a processed event with the fields we need
                processed_event = {
                    "eventID": event_id,
                    "startTime": start_time,  # Placeholder time
                    "homeTeam": home_team,
                    "awayTeam": away_team,
                    "rawData": event  # Keep the raw data for reference
                }
                
                processed_events.append(processed_event)
            
            return pd.DataFrame(processed_events)
        else:
            print("❌ No upcoming NBA games found in the next 24 hours")
            return pd.DataFrame()
    else:
        print(f"❌ Error fetching NBA events: {response.get('error')}")
        return pd.DataFrame()

def get_player_props(event_id: str) -> pd.DataFrame:
    params = {
        "eventID": event_id
    }
    
    print(f"🏀 Fetching player props data for event ID: {event_id}")
    response = make_api_request("events", params)
    
    if response.get("success"):
        events_data = response.get("data", [])
        if not events_data:
            print("❌ No event data found")
            return pd.DataFrame()
            
        event = events_data[0]
        odds_dict = event.get("odds", {})
        
        player_props = []
        for odd_id, odd_data in odds_dict.items():
            if "PLAYER" in odd_id or "_NBA" in odd_id:
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
                        "eventID": event_id
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

def parse_player_id(player_id: str) -> str:
    if not player_id or not isinstance(player_id, str):
        return "Unknown"
    
    name_parts = player_id.split("_")
    if len(name_parts) >= 3 and name_parts[-1] == "NBA":
        name_parts = name_parts[:-2]
    
    name = " ".join(name_parts).title()
    
    return name

def process_player_props(props_df: pd.DataFrame) -> pd.DataFrame:
    if props_df.empty:
        return pd.DataFrame()
    
    processed_df = props_df.copy()
    
    if "player_id" in processed_df.columns:
        processed_df["player_name"] = processed_df["player_id"].apply(parse_player_id)
    
    if "oddID" in processed_df.columns and "prop_type" not in processed_df.columns:
        processed_df["prop_details"] = processed_df["oddID"].apply(lambda x: x.split("-"))
        processed_df["prop_type"] = processed_df["prop_details"].apply(lambda x: x[0] if len(x) > 0 else "Unknown")
        processed_df["player_id"] = processed_df["prop_details"].apply(lambda x: x[1] if len(x) > 1 else "Unknown")
        processed_df["direction"] = processed_df["prop_details"].apply(lambda x: x[-1] if len(x) > 2 else "Unknown")
        processed_df["player_name"] = processed_df["player_id"].apply(parse_player_id)
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

def extract_team_name(team_data: Dict) -> str:
    if not team_data:
        return "Unknown"
    
    names = team_data.get("names", {})
    if names:
        return (names.get("medium") or 
                names.get("long") or 
                names.get("short") or 
                "Unknown")
    
    team_id = team_data.get("teamID", "")
    if team_id:
        parts = team_id.split("_")
        if len(parts) >= 2 and parts[-1] == "NBA":
            parts = parts[:-1]
            return " ".join(parts).title()
    
    return "Unknown"

def main():
    """
    Main function to fetch and process NBA player props
    """
    # Get upcoming NBA games
    games_df = get_upcoming_nba_games()
    
    if games_df.empty:
        print("❌ No upcoming NBA games found")
        return
    
    # Display the games
    print("\n📋 Upcoming NBA Games (Note: Times are placeholders):")
    for _, game in games_df.iterrows():
        try:
            # Convert UTC time to EST (these are placeholder times)
            game_time_utc = datetime.strptime(game['startTime'], "%Y-%m-%dT%H:%M:%SZ")
            game_time_est = game_time_utc.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=-5)))
            
            # Extract team names
            home_team = extract_team_name(game['homeTeam'])
            away_team = extract_team_name(game['awayTeam'])
            
            print(f"  • {game_time_est.strftime('%Y-%m-%d %I:%M %p EST')}: {away_team} @ {home_team} (ID: {game['eventID']})")
        except Exception as e:
            print(f"❌ Error displaying game: {e}")
    
    print("\n🔍 Collecting player props for all games...")
    all_props = []
    
    for _, game in games_df.iterrows():
        try:
            event_id = game['eventID']
            
            # Extract team names
            home_team = extract_team_name(game['homeTeam'])
            away_team = extract_team_name(game['awayTeam'])
            
            print(f"\n📊 Processing game: {away_team} @ {home_team} (ID: {event_id})")
            props_df = get_player_props(event_id)
            
            if props_df.empty:
                print(f"❌ No player props found for {away_team} @ {home_team}")
                continue
            
            # Process the props
            processed_props = process_player_props(props_df)
            
            if not processed_props.empty:
                # Add game information
                processed_props['home_team'] = home_team
                processed_props['away_team'] = away_team
                processed_props['game'] = f"{away_team} @ {home_team}"
                processed_props['game_number'] = event_id
                processed_props['event_id'] = event_id
                
                all_props.append(processed_props)
                
                # Print summary
                player_counts = processed_props['player_name'].value_counts()
                most_common_players = player_counts.nlargest(5)
                print(f"  • Found props for {len(player_counts)} players")
                print(f"  • Top players: {', '.join([f'{player} ({count})' for player, count in most_common_players.items()])}")
            else:
                print("❌ Failed to process player props")
        except Exception as e:
            print(f"❌ Error processing game {event_id}: {e}")
    
    if all_props:
        # Combine all props into a single DataFrame
        combined_props = pd.concat(all_props, ignore_index=True)
        
        # Save to CSV
        output_file = f"nba_player_props_{datetime.now().strftime('%Y-%m-%d')}.csv"
        combined_props.to_csv(output_file, index=False)
        print(f"\n✅ Saved {len(combined_props)} player props to {output_file}")
    else:
        print("\n❌ No player props found for any games")

if __name__ == "__main__":
    main()  # Run with EST timezone
