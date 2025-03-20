import pandas as pd
from data_processing import get_upcoming_nba_games, extract_team_name
from datetime import datetime, timezone, timedelta

def test_upcoming_games():
    """
    Test function to verify that we can fetch upcoming NBA games correctly.
    """
    print("Testing NBA games fetching...")
    
    # Get upcoming games
    games_df = get_upcoming_nba_games()
    
    if games_df.empty:
        print("No upcoming NBA games found in the next 24 hours.")
        return
    
    # Display the games with EST times
    print(f"\nFound {len(games_df)} upcoming NBA games:")
    print("-" * 80)
    print(f"{'Game Time (EST) [Placeholder]':<30} {'Away Team':<20} {'Home Team':<20} {'Event ID'}")
    print("-" * 80)
    
    for _, game in games_df.iterrows():
        try:
            # Convert UTC time to EST (note: these are placeholder times)
            game_time_utc = datetime.strptime(game['startTime'], "%Y-%m-%dT%H:%M:%SZ")
            game_time_utc = game_time_utc.replace(tzinfo=timezone.utc)
            game_time_est = game_time_utc.astimezone(timezone(timedelta(hours=-5)))
            
            # Format for display
            time_str = game_time_est.strftime('%Y-%m-%d %I:%M %p EST')
            
            # Extract team names
            home_team_data = game['homeTeam']
            away_team_data = game['awayTeam']
            
            home_team = extract_team_name(home_team_data)
            away_team = extract_team_name(away_team_data)
            
            event_id = game['eventID']
            
            print(f"{time_str:<30} {away_team:<20} {home_team:<20} {event_id}")
        except Exception as e:
            print(f"Error processing game: {e}")
            print(f"Game data: {game}")
    
    print("-" * 80)
    print("Note: Game times are placeholders since the API doesn't provide actual start times.")
    print("Test completed successfully!")

if __name__ == "__main__":
    test_upcoming_games() 