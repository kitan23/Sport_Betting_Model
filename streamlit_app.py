"""
Sports Betting Model - Streamlit Frontend

This module provides a web interface for the sports betting model using Streamlit.
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import os
import urllib.parse
from enum import Enum
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define Sport enum to match the backend
class Sport(str, Enum):
    NBA = "NBA"
    WNBA = "WNBA"
    MLB = "MLB"
    NHL = "NHL"
    INTERNATIONAL = "INTERNATIONAL"
    MLS = "MLS"
    PREMIER_LEAGUE = "PREMIER_LEAGUE"
    CHAMPIONS_LEAGUE = "CHAMPIONS_LEAGUE"

# Constants for UI
SPORT_ICONS = {
    Sport.NBA: "🏀",
    Sport.WNBA: "🏀",
    Sport.MLB: "⚾",
    Sport.NHL: "🏒",
    Sport.INTERNATIONAL: "⚽",
    Sport.MLS: "⚽",
    Sport.PREMIER_LEAGUE: "⚽",
    Sport.CHAMPIONS_LEAGUE: "⚽"
}

# Constants
# For Streamlit Cloud deployment - make API URL configurable through environment variable
# with a fallback to a deployed API URL (you'll need to deploy your FastAPI service separately)
API_URL = os.environ.get("API_URL", "http://localhost:8000")
# Remove trailing slash if present to avoid double slash issues
API_URL = API_URL.rstrip('/')
COOLDOWN_SECONDS = 180  # 3 minutes

# Set to True when running locally, False for Streamlit Cloud
LOCAL_DEV_MODE = os.environ.get("ENVIRONMENT") != "production"

# Debug logging for environment variables (only in development)
if LOCAL_DEV_MODE:
    print(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    print(f"API_URL: {API_URL}")
    print(f"LOCAL_DEV_MODE: {LOCAL_DEV_MODE}")

# Default bookmakers to show at the top of the list
DEFAULT_BOOKMAKERS = [
    "draftkings", 
    "fanduel", 
    "fanatics", 
    "caesars",
    "espnbet"
]

# Common sportsbooks
SPORTSBOOKS = [
    "draftkings", "fanduel", "fanatics", "betmgm", "caesars", "espnbet", "betrivers",
    "pinnacle", "unibet", "williamhill", "pointsbet", "twinspires", "wynnbet",
    "bet365", "bovada", "barstool", "superbook", "hardrock"
]

# Helper function to build API URL paths properly
def build_api_url(endpoint):
    """Build a properly formatted API URL by ensuring no double slashes"""
    # Ensure endpoint starts with a slash
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
    return API_URL + endpoint

def load_cached_data():
    """Load cached data from session state or file depending on environment"""
    if not LOCAL_DEV_MODE:
        # In Streamlit Cloud, use session state for persistent data
        if 'cache_data' in st.session_state:
            data = st.session_state.cache_data
            
            # Handle sport-specific refresh times
            for sport in Sport:
                # Convert timestamp string back to datetime if needed
                if f'last_refresh_{sport}' in data and data[f'last_refresh_{sport}'] and isinstance(data[f'last_refresh_{sport}'], str):
                    data[f'last_refresh_dt_{sport}'] = datetime.strptime(data[f'last_refresh_{sport}'], "%Y-%m-%d %H:%M:%S")
                
                # Ensure backward compatibility
                if f'selected_bookmaker_{sport}' in data and f'current_bookmaker_{sport}' not in data:
                    data[f'current_bookmaker_{sport}'] = data[f'selected_bookmaker_{sport}']
            
            # Handle legacy non-sport-specific data for backward compatibility
            if 'last_refresh' in data and data['last_refresh'] and isinstance(data['last_refresh'], str):
                data['last_refresh_dt'] = datetime.strptime(data['last_refresh'], "%Y-%m-%d %H:%M:%S")
                
                # Copy to NBA as default if no sport-specific data exists
                if 'last_refresh_NBA' not in data:
                    data['last_refresh_NBA'] = data['last_refresh']
                    data['last_refresh_dt_NBA'] = data['last_refresh_dt']
                
            # Ensure backward compatibility
            if 'selected_bookmaker' in data and 'current_bookmaker' not in data:
                data['current_bookmaker'] = data['selected_bookmaker']
                
                # Copy to NBA as default if no sport-specific data exists
                if 'current_bookmaker_NBA' not in data:
                    data['current_bookmaker_NBA'] = data['current_bookmaker']
                    data['selected_bookmaker_NBA'] = data['selected_bookmaker']
                
            return data
        return {}
    else:
        # Local development mode - use file
        CACHE_FILE = "streamlit_cache.json"
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    
                    # Handle sport-specific refresh times
                    for sport in Sport:
                        # Convert timestamp string back to datetime
                        if f'last_refresh_{sport}' in data and data[f'last_refresh_{sport}']:
                            data[f'last_refresh_dt_{sport}'] = datetime.strptime(data[f'last_refresh_{sport}'], "%Y-%m-%d %H:%M:%S")
                        
                        # Ensure backward compatibility
                        if f'selected_bookmaker_{sport}' in data and f'current_bookmaker_{sport}' not in data:
                            data[f'current_bookmaker_{sport}'] = data[f'selected_bookmaker_{sport}']
                    
                    # Handle legacy non-sport-specific data for backward compatibility
                    if 'last_refresh' in data and data['last_refresh']:
                        data['last_refresh_dt'] = datetime.strptime(data['last_refresh'], "%Y-%m-%d %H:%M:%S")
                        
                        # Copy to NBA as default if no sport-specific data exists
                        if 'last_refresh_NBA' not in data:
                            data['last_refresh_NBA'] = data['last_refresh']
                            data['last_refresh_dt_NBA'] = data['last_refresh_dt']
                    
                    # Ensure backward compatibility
                    if 'selected_bookmaker' in data and 'current_bookmaker' not in data:
                        data['current_bookmaker'] = data['selected_bookmaker']
                        
                        # Copy to NBA as default if no sport-specific data exists
                        if 'current_bookmaker_NBA' not in data:
                            data['current_bookmaker_NBA'] = data['current_bookmaker']
                            data['selected_bookmaker_NBA'] = data['selected_bookmaker']
                        
                    return data
            except Exception as e:
                st.error(f"Error loading cached data: {e}")
        return {}

def save_cache_data(data):
    """Save data to cache in session state or file depending on environment"""
    try:
        # Create a copy of the data to avoid modifying the original
        cache_data = data.copy()
        
        # Ensure last_refresh is saved if it exists in session state
        if 'last_refresh' not in cache_data and 'last_refresh' in st.session_state:
            cache_data['last_refresh'] = st.session_state.last_refresh
            
        # Convert datetime objects to strings
        if 'last_refresh_dt' in cache_data:
            del cache_data['last_refresh_dt']  # Remove the datetime object
            
        # Save the previous selected bookmaker for tracking
        if 'previous_selected_bookmaker' not in cache_data and 'selected_bookmaker' in cache_data:
            cache_data['previous_selected_bookmaker'] = cache_data['selected_bookmaker']
            
        # Update the cache to use current_bookmaker
        if 'selected_bookmaker' in cache_data:
            cache_data['current_bookmaker'] = cache_data['selected_bookmaker']
        
        if not LOCAL_DEV_MODE:
            # In Streamlit Cloud, use session state
            st.session_state.cache_data = cache_data
        else:
            # Local development mode - use file
            CACHE_FILE = "streamlit_cache.json"
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache_data, f)
    except Exception as e:
        st.error(f"Error saving cached data: {e}")

def button_cooldown_active(sport: Sport = Sport.NBA):
    """
    Check if the button cooldown is active for a specific sport
    
    Args:
        sport: The sport to check cooldown for
    """
    if f'last_refresh_dt_{sport}' not in st.session_state or st.session_state[f'last_refresh_dt_{sport}'] is None:
        return False
        
    elapsed = datetime.now() - st.session_state[f'last_refresh_dt_{sport}']
    return elapsed.total_seconds() < COOLDOWN_SECONDS

def get_cooldown_remaining(sport: Sport = Sport.NBA):
    """
    Get the remaining cooldown time in seconds for a specific sport
    
    Args:
        sport: The sport to get cooldown for
    """
    if f'last_refresh_dt_{sport}' not in st.session_state or st.session_state[f'last_refresh_dt_{sport}'] is None:
        return 0
        
    elapsed = datetime.now() - st.session_state[f'last_refresh_dt_{sport}']
    remaining = COOLDOWN_SECONDS - elapsed.total_seconds()
    return max(0, remaining)

def sync_with_backend_refresh_time(sport: Sport = Sport.NBA):
    """
    Sync the local cooldown timer with the backend's data refresh time for a specific sport.
    This is useful when the page is refreshed to ensure the cooldown
    timer displays the correct remaining time.
    
    Args:
        sport: The sport to sync refresh time for
    """
    if f'last_refresh_dt_{sport}' not in st.session_state:
        return
    
    # Convert sport enum to string value for API
    sport_str = str(sport.value)
        
    try:
        # Get health status from backend
        response = requests.get(build_api_url("/health"))
        if response.status_code == 200:
            health_data = response.json()
            
            if 'latest_props' in health_data and sport_str in health_data['latest_props']:
                sport_data = health_data['latest_props'][sport_str]
                
                if sport_data.get('status') == 'ok' and sport_data.get('age_minutes') is not None:
                    # Backend's props age in minutes
                    backend_age_minutes = sport_data['age_minutes']
                    
                    # Calculate the earliest refresh time
                    current_time = datetime.now()
                    backend_refresh_time = current_time - timedelta(minutes=backend_age_minutes)
                    
                    # Update local refresh time if backend data is newer
                    if (st.session_state[f'last_refresh_dt_{sport}'] is None or 
                        backend_refresh_time > st.session_state[f'last_refresh_dt_{sport}']):
                        st.session_state[f'last_refresh_dt_{sport}'] = backend_refresh_time
                        st.session_state[f'last_refresh_{sport}'] = backend_refresh_time.strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Update cache
                        if 'cache_data' in st.session_state:
                            st.session_state.cache_data[f'last_refresh_{sport}'] = st.session_state[f'last_refresh_{sport}']
    except Exception as e:
        print(f"Error syncing with backend for {sport_str}: {e}")

def main():
    st.set_page_config(
        page_title="Sports Betting Model",
        page_icon="🎮",
        layout="wide"
    )
    
    st.title("🎮 Sports Betting Model")
    st.markdown("Find value plays across different sports and bookmakers")
    
    # Display API connection status
    api_status = check_api_connection()
    if api_status:
        st.success(f"✅ Connected to API: {API_URL}")
    else:
        st.error(f"❌ Cannot connect to API: {API_URL}")
        st.warning("Please check the API URL configuration or ensure the API server is running.")
    
    # Initialize session state for sports
    if 'active_sport' not in st.session_state:
        st.session_state.active_sport = Sport.NBA
    
    # Load cached data on initial load
    if 'initialized' not in st.session_state:
        cached_data = load_cached_data()
        
        # Initialize session state with cached data
        st.session_state.last_refresh = cached_data.get('last_refresh')
        
        # Convert the string timestamp to datetime object if it exists
        if 'last_refresh' in cached_data and cached_data.get('last_refresh'):
            st.session_state.last_refresh_dt = datetime.strptime(cached_data.get('last_refresh'), "%Y-%m-%d %H:%M:%S")
        else:
            st.session_state.last_refresh_dt = None
            
        st.session_state.value_plays = cached_data.get('value_plays')
        st.session_state.current_bookmaker = cached_data.get('current_bookmaker', cached_data.get('selected_bookmaker'))
        st.session_state.previous_selected_bookmaker = cached_data.get('selected_bookmaker')
        st.session_state.is_switching_bookmakers = False  # Flag to track when we're switching bookmakers
        
        # Initialize values for each sport
        for sport in Sport:
            if f'value_plays_{sport}' not in st.session_state:
                st.session_state[f'value_plays_{sport}'] = None
            if f'last_refresh_{sport}' not in st.session_state:
                st.session_state[f'last_refresh_{sport}'] = None
            if f'last_refresh_dt_{sport}' not in st.session_state:
                st.session_state[f'last_refresh_dt_{sport}'] = None
            if f'current_bookmaker_{sport}' not in st.session_state:
                st.session_state[f'current_bookmaker_{sport}'] = cached_data.get(f'current_bookmaker_{sport}')
            if f'previous_bookmaker_{sport}' not in st.session_state:
                st.session_state[f'previous_bookmaker_{sport}'] = cached_data.get(f'previous_bookmaker_{sport}')
        
        # Initialize cache_data if not present
        if 'cache_data' not in st.session_state:
            st.session_state.cache_data = {}
            
        st.session_state.initialized = True
        
        # Sync with backend after initialization
        sync_with_backend_refresh_time(st.session_state.active_sport)
    
    # Create a sports selector at the top of the page
    st.write("## Select a Sport")
    cols = st.columns(len(Sport))
    for i, sport in enumerate(Sport):
        with cols[i]:
            selected = st.session_state.active_sport == sport
            if st.button(
                f"{SPORT_ICONS[sport]} {sport.value}", 
                key=f"sport_select_{sport}",
                use_container_width=True,
                type="primary" if selected else "secondary"
            ):
                st.session_state.active_sport = sport
                st.rerun()
    
    # Show a horizontal rule to separate sport selection from content
    st.markdown("---")
    
    # Display content for the active sport
    active_sport = st.session_state.active_sport
    st.header(f"{SPORT_ICONS[active_sport]} {active_sport.value} Value Plays")
    
    # Define callback for bookmaker selection change
    def on_bookmaker_change():
        if st.session_state[f'selected_bookmaker_{active_sport}'] != st.session_state[f'previous_bookmaker_{active_sport}']:
            st.session_state.is_switching_bookmakers = True
            st.session_state[f'current_bookmaker_{active_sport}'] = st.session_state[f'selected_bookmaker_{active_sport}']
    
    # Add information about current limitations for active sport
    if active_sport == Sport.MLB:
        st.info(f"ℹ️ **Note:** For {active_sport.value}, data is limited to the next 4 games to optimize API usage. Games are sorted by start time.")
    elif active_sport in [Sport.INTERNATIONAL, Sport.MLS, Sport.PREMIER_LEAGUE, Sport.CHAMPIONS_LEAGUE]:
        st.info(f"ℹ️ **Note:** For {active_sport.value} ⚽, this tool fetches upcoming matches for the next 24 hours. Soccer betting markets may include match result, over/under goals, and player props.")
    else:
        st.info(f"ℹ️ **Note:** This tool fetches upcoming {active_sport.value} games for the next 24 hours only.")
    
    # Sidebar for controls for active sport
    with st.sidebar:
        st.header(f"{SPORT_ICONS[active_sport]} {active_sport.value} Controls")
        
        # Sportsbook selection with popular options at top
        bookmaker_options = DEFAULT_BOOKMAKERS + [b for b in sorted(SPORTSBOOKS) if b not in DEFAULT_BOOKMAKERS]
        
        # If we're in cooldown but changing bookmaker, handle differently
        previous_bookmaker = st.session_state.get(f'previous_bookmaker_{active_sport}')
        
        # Sportsbook selection - using on_change callback
        selected_bookmaker = st.selectbox(
            "Select Sportsbook",
            bookmaker_options,
            format_func=lambda x: x.capitalize(),
            index=bookmaker_options.index(previous_bookmaker) if previous_bookmaker in bookmaker_options else 0,
            key=f"selected_bookmaker_{active_sport}",
            on_change=on_bookmaker_change
        )
        
        # Minimum edge slider
        min_edge = st.slider(
            "Minimum Edge (%)",
            min_value=0.0,
            max_value=10.0,
            value=2.0,
            step=0.5,
            key=f"min_edge_{active_sport}"
        )
        
        # Handle bookmaker change process for active sport
        if st.session_state.is_switching_bookmakers:
            # Show loading message when switching bookmakers
            with st.spinner(f"🔄 Switching to {selected_bookmaker.capitalize()}..."):
                # Process the bookmaker change
                get_value_plays(selected_bookmaker, min_edge, force_local=True, sport=active_sport)
                
                # Update tracking state
                st.session_state[f'previous_bookmaker_{active_sport}'] = selected_bookmaker
                st.session_state.is_switching_bookmakers = False
                
                # Force rerun to update UI immediately
                st.rerun()
        
        # Get props button with cooldown
        cooldown_active = button_cooldown_active(active_sport)
        cooldown_remaining = get_cooldown_remaining(active_sport)
        
        # Sync with backend for accurate cooldown timing
        if 'initialized' in st.session_state and f'last_refresh_dt_{active_sport}' in st.session_state:
            sync_with_backend_refresh_time(active_sport)
            # Recalculate cooldown after syncing
            cooldown_active = button_cooldown_active(active_sport)
            cooldown_remaining = get_cooldown_remaining(active_sport)
        
        if cooldown_active:
            remaining_mins = int(cooldown_remaining // 60)
            remaining_secs = int(cooldown_remaining % 60)
            st.warning(f"⏳ Please wait {remaining_mins}m {remaining_secs}s before refreshing")
            
            # The button exists but is disabled
            refresh_button = st.button(f"Get Fresh {active_sport.value} Props", disabled=True, key=f"refresh_disabled_{active_sport}")
            
            # Add a note about switching bookmakers
            st.caption("You can switch bookmakers while waiting by selecting a different option above")
        else:
            # Only show button when not in middle of switching bookmakers
            refresh_button = st.button(f"Get Fresh {active_sport.value} Props", key=f"refresh_enabled_{active_sport}")
            if refresh_button:
                with st.spinner(f"Fetching {active_sport.value} props data..."):
                    get_value_plays(selected_bookmaker, min_edge, sport=active_sport)
        
        # Add statistics in the sidebar for active sport
        value_plays = st.session_state.get(f'value_plays_{active_sport}')
        if value_plays and value_plays.get('stats'):
            st.divider()
            st.subheader("📊 Statistics")
            stats = value_plays.get('stats', {})
            if stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Avg Edge", f"{stats.get('avg_edge', 0):.2f}%")
                    st.metric("Avg EV", f"{stats.get('avg_ev', 0):.2f}%")
                with col2:
                    st.metric("Max Edge", f"{stats.get('max_edge', 0):.2f}%")
                    st.metric("Max EV", f"{stats.get('max_ev', 0):.2f}%")
    
    # Main content area for active sport
    current_bookmaker = st.session_state.get(f'current_bookmaker_{active_sport}', None)
    
    # Always sync with backend when displaying cooldown timer
    if 'initialized' in st.session_state and f'last_refresh_dt_{active_sport}' in st.session_state:
        sync_with_backend_refresh_time(active_sport)
    
    if current_bookmaker:
        st.subheader(f"Results for {current_bookmaker.capitalize()}")
        
    value_plays = st.session_state.get(f'value_plays_{active_sport}')
    if value_plays:
        result_container = st.container()
        with result_container:
            # Status information in a horizontal layout
            status_col1, status_col2, status_col3 = st.columns([1, 2, 1])
            with status_col1:
                st.success(f"Found {value_plays['total_plays']} value plays!")
            with status_col2:
                last_refresh = st.session_state.get(f'last_refresh_{active_sport}')
                if last_refresh:
                    st.caption(f"Last refreshed: {last_refresh}")
            with status_col3:
                # Auto-refresh countdown
                if cooldown_active:
                    # Recalculate cooldown remaining after syncing
                    cooldown_remaining = get_cooldown_remaining(active_sport)
                    st.caption(f"⏳ Next refresh in: {int(cooldown_remaining // 60)}m {int(cooldown_remaining % 60)}s")
        
        # Display the value plays
        display_value_plays(value_plays, active_sport)
    else:
        st.info(f"No {active_sport.value} data available yet. Click 'Get Fresh {active_sport.value} Props' to fetch data.")
        
        # Add a placeholder for future results
        st.caption("Results will appear here after fetching props data.")

def check_api_connection():
    """Check if the API is reachable and return status"""
    try:
        response = requests.get(build_api_url("/health"), timeout=5)
        if response.status_code == 200:
            # Try to get list of supported sports
            return True
        return False
    except:
        return False

def get_value_plays(bookmaker: str, min_edge: float, force_local: bool = False, sport: Sport = Sport.NBA):
    """
    Get value plays for a specific bookmaker and sport
    
    Args:
        bookmaker: The bookmaker to analyze
        min_edge: Minimum edge percentage to consider
        force_local: Whether to use locally cached data (for bookmaker switching during cooldown)
        sport: Sport to analyze (NBA, WNBA, MLB, NHL)
    """
    is_switching = st.session_state.get('is_switching_bookmakers', False)
    
    try:
        # Get the sport as a string value
        sport_str = str(sport.value)
    
        # For bookmaker switches during cooldown, use the latest props file without refreshing
        if force_local and f'last_props_data_time_{sport}' in st.session_state:
            print(f"Using locally cached {sport_str} props data for {bookmaker}")
            
            # Get props dataframe from session state
            if f'raw_props_df_{sport}' in st.session_state and not st.session_state[f'raw_props_df_{sport}'].empty:
                raw_props_df = st.session_state[f'raw_props_df_{sport}']
                
                # Find value plays using compare_bookmakers
                response = requests.post(
                    build_api_url(f"/value-plays/{bookmaker}/{sport_str}"),
                    params={"min_edge": min_edge},
                    json={"use_cached": True}
                )
                
                if response.status_code != 200:
                    # For Streamlit Cloud, we won't have local calculation fallback since we 
                    # don't have direct access to the comparison module
                    st.error(f"Error analyzing {sport_str} data for {bookmaker}: API returned status {response.status_code}")
                    return
                else:
                    # Update display values but keep the last refresh time from the original props fetch
                    st.session_state[f'value_plays_{sport}'] = response.json()
                    
                    # Save to cache with updated bookmaker
                    cache_data = {
                        f'value_plays_{sport}': st.session_state[f'value_plays_{sport}'],
                        f'last_refresh_{sport}': st.session_state[f'last_refresh_{sport}'],
                        f'selected_bookmaker_{sport}': bookmaker,
                        f'current_bookmaker_{sport}': bookmaker,
                        f'previous_bookmaker_{sport}': bookmaker
                    }
                    save_cache_data(cache_data)
                    
                    if is_switching:
                        st.success(f"Switched to {bookmaker.capitalize()} for {sport_str} successfully!")
                    
                    return
        
        # Get fresh data from API
        print(f"Fetching value plays for {bookmaker} in {sport_str}...")
        
        # Check for cooldown
        if button_cooldown_active(sport) and not force_local:
            remaining = get_cooldown_remaining(sport)
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            st.warning(f"⏳ Please wait {mins}m {secs}s before refreshing {sport_str} data")
            return
        
        # Fetch from API
        response = requests.get(
            build_api_url(f"/value-plays/{bookmaker}/{sport_str}"),
            params={"min_edge": min_edge}
        )
        
        # Handle API response
        if response.status_code == 200:
            # Update session state
            current_time = datetime.now()
            st.session_state[f'value_plays_{sport}'] = response.json()
            st.session_state[f'last_refresh_{sport}'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
            st.session_state[f'last_refresh_dt_{sport}'] = current_time
            st.session_state[f'last_props_data_time_{sport}'] = current_time
            
            # Get the backend's refresh time from health endpoint to sync
            try:
                health_response = requests.get(build_api_url("/health"))
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    if 'latest_props' in health_data and sport_str in health_data['latest_props']:
                        sport_data = health_data['latest_props'][sport_str]
                        if 'age_minutes' in sport_data and sport_data['age_minutes'] is not None:
                            # The backend's props data age is in minutes, convert back to a datetime
                            backend_age_minutes = sport_data['age_minutes']
                            # Calculate the backend's refresh time
                            backend_refresh_time = current_time - timedelta(minutes=backend_age_minutes)
                            # Update local refresh time if backend data is newer
                            if (st.session_state[f'last_refresh_dt_{sport}'] is None or 
                                backend_refresh_time > st.session_state[f'last_refresh_dt_{sport}']):
                                st.session_state[f'last_refresh_dt_{sport}'] = backend_refresh_time
                                st.session_state[f'last_refresh_{sport}'] = backend_refresh_time.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                print(f"Could not sync with backend refresh time for {sport_str}: {e}")
            
            # Try to save raw props data to session state by fetching the CSV file
            try:
                latest_file_response = requests.get(build_api_url(f"/latest-props-file/{sport_str}"))
                if latest_file_response.status_code == 200:
                    file_info = latest_file_response.json()
                    # For Streamlit Cloud, we don't save the actual file path since we can't access it
                    st.session_state[f'latest_props_info_{sport}'] = file_info
            except Exception as e:
                print(f"Could not get latest props file for {sport_str}: {e}")
            
            # Cache the data - only save JSON serializable values
            cache_data = {
                f'value_plays_{sport}': st.session_state[f'value_plays_{sport}'],
                f'last_refresh_{sport}': st.session_state[f'last_refresh_{sport}'],
                f'selected_bookmaker_{sport}': bookmaker,
                f'current_bookmaker_{sport}': bookmaker,
                f'previous_bookmaker_{sport}': bookmaker
            }
            save_cache_data(cache_data)
            
            st.success(f"Found {st.session_state[f'value_plays_{sport}']['total_plays']} value plays for {sport_str}!")
        else:
            st.error(f"Error getting {sport_str} value plays: {response.text}")
    except Exception as e:
        st.error(f"Error connecting to API for {sport}: {str(e)}")
        print(f"Detailed API error for {sport}: {str(e)}")

def display_value_plays(value_plays: dict, sport: Sport = Sport.NBA):
    """Display the value plays in a nice format"""
    if not value_plays or not value_plays.get("plays"):
        st.info(f"No value plays found for {sport} with the selected criteria")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(value_plays["plays"])
    
    # Format columns
    if 'target_odds' in df.columns:
        df['target_odds'] = df['target_odds'].apply(
            lambda x: f"+{int(x)}" if x > 0 else f"{int(x)}"
        )
    
    if 'median_odds' in df.columns:
        df['median_odds'] = df['median_odds'].apply(
            lambda x: f"+{int(x)}" if pd.notna(x) else "N/A"
        )
    
    if 'edge' in df.columns:
        df['edge'] = df['edge'].apply(lambda x: f"{x:.2f}%")
    
    if 'ev_percentage' in df.columns:
        df['ev_percentage'] = df['ev_percentage'].apply(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
        )
    
    # Display the data
    st.dataframe(
        df,
        column_config={
            "player": "Player",
            "prop_type": "Prop Type",
            "line": "Line",
            "direction": "Direction",
            "target_odds": "Odds",
            "median_odds": "Market Odds",
            "median_bookmaker": "Compared To",
            "edge": "Edge",
            "ev_percentage": "EV",
            "game": "Game",
            "comparison_type": "Comparison Type",
            "recommendation": "Recommendation",
            "other_bookmakers_lines": "Other Bookmakers",
            "num_bookmakers": "Book Count"
        },
        hide_index=True
    )
    
    # Download button
    csv = df.to_csv(index=False)
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    bookmaker = value_plays.get('bookmaker', 'unknown')
    
    st.download_button(
        label=f"Download {sport.value} Value Plays CSV",
        data=csv,
        file_name=f"{sport.value.lower()}_{bookmaker}_value_plays_{current_time}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main() 