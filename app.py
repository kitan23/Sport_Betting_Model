"""
Sports Betting Model - FastAPI Backend

This module provides API endpoints for the sports betting model web application.
It follows the standard workflow: 
1. data_processing.py generates a CSV file with all props
2. compare_bookmakers.py analyzes the CSV for a specific bookmaker
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import List, Dict, Optional
import data_processing as dp
import compare_bookmakers as cb
from datetime import datetime
import os
import tempfile
import numpy as np
from enum import Enum
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the CSV storage path from environment variable or use default
CSV_STORAGE_PATH = os.environ.get("CSV_STORAGE_PATH", ".")
# Create the directory if it doesn't exist
os.makedirs(CSV_STORAGE_PATH, exist_ok=True)

# Debug logging for environment variables (only in development)
if os.environ.get("ENVIRONMENT") != "production":
    print(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    print(f"CSV_STORAGE_PATH: {CSV_STORAGE_PATH}")

# Define supported sports
class Sport(str, Enum):
    NBA = "NBA"
    WNBA = "WNBA"
    MLB = "MLB"
    NHL = "NHL"
    INTERNATIONAL = "INTERNATIONAL"
    MLS = "MLS"
    PREMIER_LEAGUE = "PREMIER_LEAGUE"
    CHAMPIONS_LEAGUE = "CHAMPIONS_LEAGUE"

app = FastAPI(title="Sports Betting Model API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to track latest props data files for each sport
latest_props_files = {sport: None for sport in Sport}
latest_props_times = {sport: None for sport in Sport}

@app.get("/")
async def root():
    """Root endpoint returning API status"""
    return {"status": "active", "message": "Sports Betting Model API is running"}

@app.get("/bookmakers/{sport}")
async def get_bookmakers(sport: Sport = Sport.NBA):
    """Get list of available bookmakers for a specific sport"""
    try:
        # Ensure we have fresh data
        props_file = await refresh_props_data(sport)
        
        if not props_file or not os.path.exists(props_file):
            raise HTTPException(status_code=500, detail=f"No props data available for {sport}")
            
        # Read the CSV file
        props_df = pd.read_csv(props_file)
        
        # Extract bookmakers using compare_bookmakers.py function
        print(f"🔍 Extracting available bookmakers from props file for {sport}...")
        bookmakers = cb.extract_bookmaker_from_raw_props(props_df)
        print(f"✅ Found {len(bookmakers)} bookmakers for {sport}")
        
        return {"bookmakers": bookmakers}
    except Exception as e:
        print(f"❌ Error getting bookmakers for {sport}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/value-plays/{bookmaker}/{sport}")
async def get_value_plays(bookmaker: str, sport: Sport = Sport.NBA, min_edge: float = 2.0):
    """
    Get value plays for a specific bookmaker and sport
    
    Args:
        bookmaker: Name of the bookmaker to analyze
        sport: Sport to analyze (NBA, WNBA, MLB, NHL)
        min_edge: Minimum edge percentage to consider (default: 2.0)
    """
    try:
        print(f"\n🔍 Getting value plays for {bookmaker} in {sport} (min edge: {min_edge}%)")
        
        # Ensure we have fresh data
        props_file = await refresh_props_data(sport)
        
        if not props_file or not os.path.exists(props_file):
            raise HTTPException(status_code=500, detail=f"No props data available for {sport}")
            
        print(f"📊 Analyzing props from {props_file}")
        
        # Use analyze_csv_structure to properly format the data
        # This is the same method compare_bookmakers.py uses
        props_df = cb.analyze_csv_structure(props_file)
        
        if props_df is None or props_df.empty:
            raise HTTPException(status_code=500, detail="Could not process the CSV file")
        
        # Get available bookmakers to validate the requested one
        available_bookmakers = cb.extract_bookmaker_from_raw_props(props_df)
        
        if not available_bookmakers:
            raise HTTPException(status_code=500, detail="No bookmakers found in the data")
        
        print(f"📋 Available bookmakers: {', '.join(available_bookmakers[:5])}...")
        
        # Check if the requested bookmaker exists
        if bookmaker not in available_bookmakers:
            # Try case-insensitive match
            bookmaker_lower = bookmaker.lower()
            matched_bookmaker = next((b for b in available_bookmakers if b.lower() == bookmaker_lower), None)
            
            if matched_bookmaker:
                print(f"ℹ️ Using '{matched_bookmaker}' instead of '{bookmaker}'")
                bookmaker = matched_bookmaker
            else:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Bookmaker '{bookmaker}' not found. Available: {', '.join(available_bookmakers)}"
                )
        
        # Use compare_bookmakers.py to analyze the data for the specified bookmaker
        print(f"🔍 Searching for value plays for {bookmaker}...")
        value_plays = cb.find_value_plays_raw(props_df, bookmaker, min_edge)
        
        # Format for frontend
        if not value_plays.empty:
            # Convert to dict for JSON serialization and sanitize NaN values
            sanitized_plays = sanitize_for_json(value_plays.to_dict(orient='records'))
            
            # Format the data for better display
            formatted_data = cb.format_for_export(value_plays)
            
            print(f"✅ Found {len(sanitized_plays)} value plays for {bookmaker} in {sport}")
            
            # Categorize value plays for summary
            same_line_plays = value_plays[value_plays['comparison_type'] == 'same line comparison'] if 'comparison_type' in value_plays.columns else pd.DataFrame()
            line_shopping_plays = value_plays[value_plays['comparison_type'].str.contains('line shopping', na=False)] if 'comparison_type' in value_plays.columns else pd.DataFrame()
            
            # Print summary similar to compare_bookmakers.py
            if not same_line_plays.empty:
                print(f"  - {len(same_line_plays)} plays with odds advantage (same line)")
            if not line_shopping_plays.empty:
                print(f"  - {len(line_shopping_plays)} plays with line shopping advantage")
            
            # Add summary statistics
            stats = {}
            if 'edge' in value_plays.columns:
                avg_edge = float(value_plays['edge'].mean())
                max_edge = float(value_plays['edge'].max())
                min_edge = float(value_plays['edge'].min())
                stats.update({
                    "avg_edge": 0.0 if pd.isna(avg_edge) else avg_edge,
                    "max_edge": 0.0 if pd.isna(max_edge) else max_edge,
                    "min_edge": 0.0 if pd.isna(min_edge) else min_edge,
                })
            
            if 'ev_percentage' in value_plays.columns:
                avg_ev = float(value_plays['ev_percentage'].mean())
                max_ev = float(value_plays['ev_percentage'].max())
                stats.update({
                    "avg_ev": 0.0 if pd.isna(avg_ev) else avg_ev,
                    "max_ev": 0.0 if pd.isna(max_ev) else max_ev,
                })
            
            # Make sure the entire response is sanitized
            response = {
                "bookmaker": bookmaker,
                "sport": sport,
                "min_edge": min_edge,
                "total_plays": len(sanitized_plays),
                "plays": sanitized_plays,
                "stats": stats
            }
            
            return sanitize_for_json(response)
        else:
            print(f"ℹ️ No value plays found for {bookmaker} in {sport} with min edge of {min_edge}%")
            return {
                "bookmaker": bookmaker,
                "sport": sport,
                "min_edge": min_edge,
                "total_plays": 0,
                "plays": []
            }
    except Exception as e:
        print(f"❌ Error finding value plays: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/latest-props-file/{sport}")
async def get_latest_props_file(sport: Sport = Sport.NBA):
    """Get the path to the latest props file for a specific sport without refreshing the data"""
    global latest_props_files, latest_props_times
    
    if not latest_props_files[sport] or not os.path.exists(latest_props_files[sport]):
        raise HTTPException(status_code=404, detail=f"No props data available for {sport}")
        
    age_seconds = (datetime.now() - latest_props_times[sport]).total_seconds() if latest_props_times[sport] else 0
    
    return {
        "file_path": latest_props_files[sport],
        "last_updated": latest_props_times[sport].strftime("%Y-%m-%d %H:%M:%S") if latest_props_times[sport] else None,
        "age_minutes": int(age_seconds / 60),
        "sport": sport
    }

@app.post("/value-plays/{bookmaker}/{sport}")
async def post_value_plays(
    bookmaker: str,
    sport: Sport = Sport.NBA, 
    min_edge: float = 2.0, 
    request_data: Optional[Dict] = Body(None)
):
    """
    Alternative endpoint to get value plays that can use cached data
    
    This endpoint allows the frontend to send a POST request with the use_cached flag
    to analyze existing props data with a different bookmaker during cooldown periods.
    """
    try:
        use_cached = False
        if request_data and "use_cached" in request_data:
            use_cached = request_data["use_cached"]
        
        # Always use the latest props file for the specified sport
        props_file = latest_props_files[sport]
        
        if not props_file or not os.path.exists(props_file):
            if use_cached:
                # If we're trying to use cached data but there is none, return an error
                raise HTTPException(
                    status_code=404, 
                    detail=f"No cached props data available for {sport}."
                )
            else:
                # Otherwise fetch new data
                props_file = await refresh_props_data(sport)
                
                if not props_file:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Failed to fetch props data for {sport}."
                    )
        
        # Read the props data CSV
        print(f"📊 Using props from {props_file} for bookmaker {bookmaker} in {sport}")
        props_df = cb.analyze_csv_structure(props_file)
        
        # Find value plays
        value_plays = cb.find_value_plays_raw(props_df, bookmaker, min_edge)
        
        # Calculate stats and format response
        if not value_plays.empty:
            # Convert to dict for JSON serialization and sanitize NaN values
            sanitized_plays = sanitize_for_json(value_plays.to_dict(orient='records'))
            
            # Add summary statistics
            stats = {}
            if 'edge' in value_plays.columns:
                avg_edge = float(value_plays['edge'].mean())
                max_edge = float(value_plays['edge'].max())
                min_edge = float(value_plays['edge'].min())
                stats.update({
                    "avg_edge": 0.0 if pd.isna(avg_edge) else avg_edge,
                    "max_edge": 0.0 if pd.isna(max_edge) else max_edge,
                    "min_edge": 0.0 if pd.isna(min_edge) else min_edge,
                })
            
            if 'ev_percentage' in value_plays.columns:
                avg_ev = float(value_plays['ev_percentage'].mean())
                max_ev = float(value_plays['ev_percentage'].max())
                stats.update({
                    "avg_ev": 0.0 if pd.isna(avg_ev) else avg_ev,
                    "max_ev": 0.0 if pd.isna(max_ev) else max_ev,
                })
            
            response = {
                "bookmaker": bookmaker,
                "sport": sport,
                "min_edge": min_edge,
                "total_plays": len(sanitized_plays),
                "plays": sanitized_plays,
                "stats": stats
            }
            
            return sanitize_for_json(response)
        else:
            print(f"ℹ️ No value plays found for {bookmaker} in {sport} with min edge of {min_edge}%")
            return {
                "bookmaker": bookmaker,
                "sport": sport,
                "min_edge": min_edge,
                "total_plays": 0,
                "plays": []
            }
    except Exception as e:
        print(f"❌ Error finding value plays with POST: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    current_time = datetime.now()
    
    # Check data directory
    storage_status = "ok" if os.path.exists(CSV_STORAGE_PATH) and os.access(CSV_STORAGE_PATH, os.W_OK) else "error"
    
    # Check latest props files for each sport
    props_status = {}
    for sport in Sport:
        sport_props_file = latest_props_files[sport]
        sport_props_time = latest_props_times[sport]
        
        status = "ok" if sport_props_file and os.path.exists(sport_props_file) else "not_available"
        props_age_minutes = None
        if sport_props_time:
            props_age_minutes = int((current_time - sport_props_time).total_seconds() / 60)
        
        props_status[sport] = {
            "status": status,
            "age_minutes": props_age_minutes,
            "file_path": sport_props_file
        }
    
    return {
        "status": "healthy",
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "storage": {
            "path": CSV_STORAGE_PATH,
            "status": storage_status
        },
        "latest_props": props_status
    }

async def refresh_props_data(sport: Sport = Sport.NBA):
    """
    Run data_processing.py to get fresh props data and save to CSV for a specific sport.
    Refreshes if data is older than 3 minutes.
    
    Args:
        sport: Sport to fetch data for (NBA, WNBA, MLB, NHL)
        
    Returns:
        Path to the CSV file containing props data
    """
    global latest_props_files, latest_props_times
    
    current_time = datetime.now()
    
    # Refresh if data is None or older than 3 minutes
    if (latest_props_files[sport] is None or 
        latest_props_times[sport] is None or 
        (current_time - latest_props_times[sport]).total_seconds() > 180 or
        not os.path.exists(latest_props_files[sport])):
        
        print(f"\n🔄 Generating fresh props data for {sport}...")
        
        # Create the CSV file path using the storage path from environment
        csv_file = os.path.join(CSV_STORAGE_PATH, f"{sport.lower()}_player_props_{current_time.strftime('%Y-%m-%d_%H%M%S')}.csv")
        
        try:
            # Get upcoming games for the specified sport
            print(f"📅 Step 1: Fetching upcoming {sport} games...")
            games_df = dp.get_upcoming_games(str(sport.value))
            
            if games_df.empty:
                raise HTTPException(status_code=500, detail=f"No upcoming {sport} games found")
            
            # Limit MLB games to a maximum of 4 to conserve API calls
            game_limit = 4 if sport == Sport.MLB else len(games_df)
            if sport == Sport.MLB and len(games_df) > game_limit:
                print(f"⚾ Limiting MLB games to {game_limit} (out of {len(games_df)} available)")
                games_df = games_df.head(game_limit)
                
            # Get props for all games
            all_props = []
            
            print(f"🏀 Step 2: Fetching player props for {len(games_df)} {sport} games...")
            
            # Process each game to get player props
            for idx, game in games_df.iterrows():
                try:
                    event_id = game['eventID']
                    
                    # Extract team names using the function directly from data_processing
                    # Note that we need to pass the league to extract_team_name
                    home_team = dp.extract_team_name(game['homeTeam'], str(sport.value))
                    away_team = dp.extract_team_name(game['awayTeam'], str(sport.value))
                    
                    print(f"  • Game {idx+1}/{len(games_df)}: {away_team} @ {home_team} (ID: {event_id})")
                    
                    # Get player props for this game
                    props_df = dp.get_player_props(event_id, home_team, away_team, str(sport.value))
                    
                    if not props_df.empty:
                        # Process the props
                        processed_props = dp.process_player_props(props_df)
                        
                        if not processed_props.empty:
                            # Add game information
                            processed_props['home_team'] = home_team
                            processed_props['away_team'] = away_team
                            processed_props['game'] = f"{away_team} @ {home_team}"
                            processed_props['game_number'] = event_id
                            processed_props['event_id'] = event_id
                            processed_props['league'] = str(sport.value)
                            
                            prop_count = len(processed_props)
                            all_props.append(processed_props)
                            print(f"    ✅ Added {prop_count} props for this game")
                        else:
                            print(f"    ⚠️ No usable props found for this game")
                    else:
                        print(f"    ⚠️ No raw props found for this game")
                except Exception as e:
                    print(f"    ❌ Error processing {sport} game {event_id}: {e}")
                    continue
            
            if all_props:
                # Combine all props
                print(f"\n📊 Step 3: Combining and saving {sport} player props...")
                combined_props = pd.concat(all_props, ignore_index=True)
                
                # Save to CSV
                combined_props.to_csv(csv_file, index=False)
                
                total_props = len(combined_props)
                print(f"✅ Generated {total_props} {sport} props and saved to {csv_file}")
                
                # Update global variables
                latest_props_files[sport] = csv_file
                latest_props_times[sport] = current_time
                
                return csv_file
            else:
                print(f"❌ No props found for any {sport} games")
                raise HTTPException(status_code=500, detail=f"No props found for any {sport} games")
        
        except Exception as e:
            print(f"❌ Error generating {sport} props data: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        age_seconds = (current_time - latest_props_times[sport]).total_seconds()
        print(f"ℹ️ Using existing {sport} props file: {latest_props_files[sport]} (age: {int(age_seconds/60)} minutes)")
    
    # Return existing file if it's still fresh
    return latest_props_files[sport]

# Add a new helper function at the top level to handle NaN values in JSON
def sanitize_for_json(obj):
    """
    Recursively sanitize an object for JSON serialization by replacing NaN values.
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, (pd.Series, pd.DataFrame)):
        return sanitize_for_json(obj.to_dict())
    elif isinstance(obj, float) and (pd.isna(obj) or np.isnan(obj)):
        return 0.0
    else:
        return obj

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Sports Betting Model API Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 