"""
Sports Betting Model - Fetch Specific Games Module

This module contains functions to fetch player props for specific games
and append them to an existing CSV file, with rate limiting to avoid API errors.
"""

import requests
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta, timezone
import time
from typing import Dict, List, Any, Optional, Union
import random

# Import functions from data_processing.py
from data_processing import (
    API_KEY, BASE_URL, HEADERS,
    process_player_props, parse_player_id,
    extract_team_name, convert_american_to_decimal,
    calculate_implied_probability
)

def make_api_request_with_retry(endpoint: str, params: Dict = None, max_retries: int = 5, base_delay: float = 2.0) -> Dict:
    """
    Make an API request with exponential backoff retry logic to handle rate limiting.
    
    Args:
        endpoint: API endpoint to call
        params: Query parameters
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries (will be exponentially increased)
        
    Returns:
        API response as dictionary
    """
    url = f"{BASE_URL}/{endpoint}"
    print(f"Making request to: {url}")
    
    for attempt in range(max_retries):
        try:
            # Add a small random delay before each request to avoid hitting rate limits
            jitter = random.uniform(0.1, 0.5)
            time.sleep(base_delay + jitter)
            
            response = requests.get(url, headers=HEADERS, params=params)
            response.raise_for_status()
            
            # Success - return the response
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:  # Too Many Requests
                # Calculate exponential backoff delay
                delay = base_delay * (2 ** attempt) + random.uniform(0.1, 1.0)
                print(f"Rate limit hit. Retrying in {delay:.2f} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(delay)
            else:
                print(f"HTTP Error: {e}")
                return {"success": False, "error": str(e)}
                
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            return {"success": False, "error": str(e)}
    
    # If we've exhausted all retries
    print(f"Failed after {max_retries} attempts")
    return {"success": False, "error": f"Failed after {max_retries} attempts"}

def get_player_props_for_game(event_id: str) -> pd.DataFrame:
    """
    Get player props for a specific game with retry logic.
    
    Args:
        event_id: The event ID of the game
        
    Returns:
        DataFrame containing player props
    """
    params = {
        "eventID": event_id
    }
    
    print(f"Fetching player props for event {event_id}")
    response = make_api_request_with_retry("events", params)
    
    if not response.get("success", True):  # If success key exists and is False
        print(f"Error fetching event: {response.get('error')}")
        return pd.DataFrame()
        
    events_data = response.get("data", [])
    if not events_data:
        print("No event data found")
        return pd.DataFrame()
        
    event = events_data[0]
    odds_dict = event.get("odds", {})
    
    # Extract team names from the teams object in the response
    home_team = "Unknown"
    away_team = "Unknown"
    
    if "teams" in event:
        teams_data = event.get("teams", {})
        if "home" in teams_data and "names" in teams_data["home"]:
            home_names = teams_data["home"]["names"]
            home_team = home_names.get("long", home_names.get("location", "Unknown"))
        
        if "away" in teams_data and "names" in teams_data["away"]:
            away_names = teams_data["away"]["names"]
            away_team = away_names.get("long", away_names.get("location", "Unknown"))
    
    game_name = f"{away_team} @ {home_team}"
    print(f"Processing props for {game_name}")
    
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
    
    props_df = pd.DataFrame(player_props)
    
    if props_df.empty:
        print(f"No player props found for {game_name}")
        return pd.DataFrame()
    
    # Process the props
    processed_props = process_player_props(props_df)
    
    if not processed_props.empty:
        # Add game information
        processed_props['home_team'] = home_team
        processed_props['away_team'] = away_team
        processed_props['game'] = game_name
        processed_props['game_number'] = event_id
        processed_props['event_id'] = event_id
        
        # Print summary
        player_counts = processed_props['player_name'].value_counts()
        print(f"\nPlayer Props Summary for {game_name}:")
        for player, count in player_counts.items():
            print(f"- {player}: {count} props")
            
        return processed_props
    
    return pd.DataFrame()

def fetch_and_append_games(event_ids: List[str], output_csv: str = None) -> str:
    """
    Fetch player props for specific games and append them to an existing CSV file.
    
    Args:
        event_ids: List of event IDs to fetch
        output_csv: Path to the output CSV file (if None, will use today's date)
        
    Returns:
        Path to the updated CSV file
    """
    # Determine output file
    if output_csv is None:
        output_csv = f"nba_player_props_{datetime.now().strftime('%Y-%m-%d')}.csv"
    
    # Check if the file exists
    file_exists = os.path.isfile(output_csv)
    
    # Load existing data if file exists
    existing_data = pd.DataFrame()
    if file_exists:
        try:
            existing_data = pd.read_csv(output_csv)
            print(f"Loaded existing data from {output_csv} with {len(existing_data)} rows")
        except Exception as e:
            print(f"Error loading existing data: {e}")
            file_exists = False
    
    # Fetch props for each game
    all_new_props = []
    
    for event_id in event_ids:
        try:
            print(f"\nProcessing game with event ID: {event_id}")
            props_df = get_player_props_for_game(event_id)
            
            if not props_df.empty:
                print(f"Found {len(props_df)} player props for event {event_id}")
                all_new_props.append(props_df)
            else:
                print(f"No player props found for event {event_id}")
        except Exception as e:
            print(f"Error processing game {event_id}: {e}")
    
    if not all_new_props:
        print("No new player props found")
        return output_csv
    
    # Combine all new props
    new_props_df = pd.concat(all_new_props, ignore_index=True)
    print(f"Total new props: {len(new_props_df)}")
    
    # Combine with existing data or save as new file
    if file_exists and not existing_data.empty:
        # Check for duplicates based on oddID if it exists
        if 'oddID' in existing_data.columns and 'oddID' in new_props_df.columns:
            # Get oddIDs that are already in the existing data
            existing_odd_ids = set(existing_data['oddID'])
            # Filter out props that are already in the existing data
            new_props_df = new_props_df[~new_props_df['oddID'].isin(existing_odd_ids)]
            print(f"After removing duplicates: {len(new_props_df)} new props")
        
        # Combine and save
        combined_df = pd.concat([existing_data, new_props_df], ignore_index=True)
        combined_df.to_csv(output_csv, index=False)
        print(f"Appended {len(new_props_df)} new props to {output_csv}")
    else:
        # Save as new file
        new_props_df.to_csv(output_csv, index=False)
        print(f"Saved {len(new_props_df)} props to new file {output_csv}")
    
    return output_csv

if __name__ == "__main__":
    # List of event IDs for games that failed to fetch due to rate limiting
    event_ids = [
        "IVxzJFHamEtDkWDHa4vt"
    ]
    
    # Specify the CSV file to append to
    csv_file = "nba_player_props_2025-04-29.csv"
    
    print(f"Fetching player props for {len(event_ids)} games and appending to {csv_file}...")
    output_file = fetch_and_append_games(event_ids, csv_file)
    print(f"Process completed. Updated file: {output_file}") 