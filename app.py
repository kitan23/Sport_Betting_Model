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

# Get the CSV storage path from environment variable or use default
CSV_STORAGE_PATH = os.environ.get("CSV_STORAGE_PATH", ".")
# Create the directory if it doesn't exist
os.makedirs(CSV_STORAGE_PATH, exist_ok=True)

app = FastAPI(title="Sports Betting Model API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to track latest props data file
latest_props_file = None
latest_props_time = None

@app.get("/")
async def root():
    """Root endpoint returning API status"""
    return {"status": "active", "message": "Sports Betting Model API is running"}

@app.get("/bookmakers")
async def get_bookmakers():
    """Get list of available bookmakers"""
    try:
        # Ensure we have fresh data
        props_file = await refresh_props_data()
        
        if not props_file or not os.path.exists(props_file):
            raise HTTPException(status_code=500, detail="No props data available")
            
        # Read the CSV file
        props_df = pd.read_csv(props_file)
        
        # Extract bookmakers using compare_bookmakers.py function
        print(f"🔍 Extracting available bookmakers from props file...")
        bookmakers = cb.extract_bookmaker_from_raw_props(props_df)
        print(f"✅ Found {len(bookmakers)} bookmakers")
        
        return {"bookmakers": bookmakers}
    except Exception as e:
        print(f"❌ Error getting bookmakers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/value-plays/{bookmaker}")
async def get_value_plays(bookmaker: str, min_edge: float = 2.0):
    """
    Get value plays for a specific bookmaker
    
    Args:
        bookmaker: Name of the bookmaker to analyze
        min_edge: Minimum edge percentage to consider (default: 2.0)
    """
    try:
        print(f"\n🔍 Getting value plays for {bookmaker} (min edge: {min_edge}%)")
        
        # Ensure we have fresh data
        props_file = await refresh_props_data()
        
        if not props_file or not os.path.exists(props_file):
            raise HTTPException(status_code=500, detail="No props data available")
            
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
            
            print(f"✅ Found {len(sanitized_plays)} value plays for {bookmaker}")
            
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
                "min_edge": min_edge,
                "total_plays": len(sanitized_plays),
                "plays": sanitized_plays,
                "stats": stats
            }
            
            return sanitize_for_json(response)
        else:
            print(f"ℹ️ No value plays found for {bookmaker} with min edge of {min_edge}%")
            return {
                "bookmaker": bookmaker,
                "min_edge": min_edge,
                "total_plays": 0,
                "plays": []
            }
    except Exception as e:
        print(f"❌ Error finding value plays: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/latest-props-file")
async def get_latest_props_file():
    """Get the path to the latest props file without refreshing the data"""
    global latest_props_file, latest_props_time
    
    if not latest_props_file or not os.path.exists(latest_props_file):
        raise HTTPException(status_code=404, detail="No props data available")
        
    age_seconds = (datetime.now() - latest_props_time).total_seconds() if latest_props_time else 0
    
    return {
        "file_path": latest_props_file,
        "last_updated": latest_props_time.strftime("%Y-%m-%d %H:%M:%S") if latest_props_time else None,
        "age_minutes": int(age_seconds / 60)
    }

@app.post("/value-plays/{bookmaker}")
async def post_value_plays(
    bookmaker: str, 
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
        
        # Always use the latest props file
        props_file = latest_props_file
        
        if not props_file or not os.path.exists(props_file):
            if use_cached:
                # If we're trying to use cached data but there is none, return an error
                raise HTTPException(
                    status_code=404, 
                    detail="No cached props data available."
                )
            else:
                # Otherwise fetch new data
                props_file = await refresh_props_data()
                
                if not props_file:
                    raise HTTPException(
                        status_code=404, 
                        detail="Failed to fetch props data."
                    )
        
        # Read the props data CSV
        print(f"📊 Using props from {props_file} for bookmaker {bookmaker}")
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
                "min_edge": min_edge,
                "total_plays": len(sanitized_plays),
                "plays": sanitized_plays,
                "stats": stats
            }
            
            return sanitize_for_json(response)
        else:
            print(f"ℹ️ No value plays found for {bookmaker} with min edge of {min_edge}%")
            return {
                "bookmaker": bookmaker,
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
    
    # Check latest props file
    props_status = "ok" if latest_props_file and os.path.exists(latest_props_file) else "not_available"
    props_age_minutes = None
    if latest_props_time:
        props_age_minutes = int((current_time - latest_props_time).total_seconds() / 60)
    
    return {
        "status": "healthy",
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "storage": {
            "path": CSV_STORAGE_PATH,
            "status": storage_status
        },
        "latest_props": {
            "status": props_status,
            "age_minutes": props_age_minutes
        }
    }

async def refresh_props_data():
    """
    Run data_processing.py to get fresh props data and save to CSV.
    Refreshes if data is older than 5 minutes.
    
    Returns:
        Path to the CSV file containing props data
    """
    global latest_props_file, latest_props_time
    
    current_time = datetime.now()
    
    # Refresh if data is None or older than 5 minutes
    if (latest_props_file is None or 
        latest_props_time is None or 
        (current_time - latest_props_time).total_seconds() > 300 or
        not os.path.exists(latest_props_file)):
        
        print("\n🔄 Generating fresh props data...")
        
        # Create the CSV file path using the storage path from environment
        csv_file = os.path.join(CSV_STORAGE_PATH, f"nba_player_props_{current_time.strftime('%Y-%m-%d_%H%M%S')}.csv")
        
        try:
            # Get upcoming games
            print("📅 Step 1: Fetching upcoming NBA games...")
            games_df = dp.get_upcoming_nba_games()
            
            if games_df.empty:
                raise HTTPException(status_code=500, detail="No upcoming games found")
                
            # Get props for all games
            all_props = []
            
            print(f"🏀 Step 2: Fetching player props for {len(games_df)} games...")
            
            # Process each game to get player props
            for idx, game in games_df.iterrows():
                try:
                    event_id = game['eventID']
                    
                    # Extract team names using the function directly from data_processing
                    from data_processing import extract_team_name
                    home_team = extract_team_name(game['homeTeam'])
                    away_team = extract_team_name(game['awayTeam'])
                    
                    print(f"  • Game {idx+1}/{len(games_df)}: {away_team} @ {home_team} (ID: {event_id})")
                    
                    # Get player props for this game
                    props_df = dp.get_player_props(event_id)
                    
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
                            
                            prop_count = len(processed_props)
                            all_props.append(processed_props)
                            print(f"    ✅ Added {prop_count} props for this game")
                        else:
                            print(f"    ⚠️ No usable props found for this game")
                    else:
                        print(f"    ⚠️ No raw props found for this game")
                except Exception as e:
                    print(f"    ❌ Error processing game {event_id}: {e}")
                    continue
            
            if all_props:
                # Combine all props
                print("\n📊 Step 3: Combining and saving player props...")
                combined_props = pd.concat(all_props, ignore_index=True)
                
                # Save to CSV
                combined_props.to_csv(csv_file, index=False)
                
                total_props = len(combined_props)
                print(f"✅ Generated {total_props} props and saved to {csv_file}")
                
                # Update global variables
                latest_props_file = csv_file
                latest_props_time = current_time
                
                return csv_file
            else:
                print("❌ No props found for any games")
                raise HTTPException(status_code=500, detail="No props found for any games")
        
        except Exception as e:
            print(f"❌ Error generating props data: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        age_seconds = (current_time - latest_props_time).total_seconds()
        print(f"ℹ️ Using existing props file: {latest_props_file} (age: {int(age_seconds/60)} minutes)")
    
    # Return existing file if it's still fresh
    return latest_props_file

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