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

# Constants
# For Streamlit Cloud deployment - make API URL configurable through environment variable
# with a fallback to a deployed API URL (you'll need to deploy your FastAPI service separately)
API_URL = os.environ.get("API_URL", "https://sport-betting-model.onrender.com")
# Remove trailing slash if present to avoid double slash issues
API_URL = API_URL.rstrip('/')
COOLDOWN_SECONDS = 600  # 10 minutes

# Set to True when running locally, False for Streamlit Cloud
LOCAL_DEV_MODE = False

# Available sportsbooks
SPORTSBOOKS = [
    "ballybet",
    "bet365",
    "betmgm",
    "betonline",
    "betparx",
    "betrivers",
    "bookmakereu",
    "bovada",
    "caesars",
    "draftkings",
    "espnbet",
    "fanatics",
    "fanduel",
    "fliff",
    "fourwinds",
    "hardrockbet",
    "pinnacle",
    "prizepicks",
    "prophetexchange",
    "underdog",
]

# Default popular bookmakers to show at the top of the list
DEFAULT_BOOKMAKERS = ["draftkings", "fanduel", "fanatics", "betmgm", "caesars"]

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
            
            # Convert timestamp string back to datetime if needed
            if 'last_refresh' in data and data['last_refresh'] and isinstance(data['last_refresh'], str):
                data['last_refresh_dt'] = datetime.strptime(data['last_refresh'], "%Y-%m-%d %H:%M:%S")
                
            # Ensure backward compatibility
            if 'selected_bookmaker' in data and 'current_bookmaker' not in data:
                data['current_bookmaker'] = data['selected_bookmaker']
                
            return data
        return {}
    else:
        # Local development mode - use file
        CACHE_FILE = "streamlit_cache.json"
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    
                    # Convert timestamp string back to datetime
                    if 'last_refresh' in data and data['last_refresh']:
                        data['last_refresh_dt'] = datetime.strptime(data['last_refresh'], "%Y-%m-%d %H:%M:%S")
                    
                    # Ensure backward compatibility
                    if 'selected_bookmaker' in data and 'current_bookmaker' not in data:
                        data['current_bookmaker'] = data['selected_bookmaker']
                        
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

def button_cooldown_active():
    """Check if the button cooldown is active"""
    if 'last_refresh_dt' not in st.session_state or st.session_state.last_refresh_dt is None:
        return False
        
    elapsed = datetime.now() - st.session_state.last_refresh_dt
    return elapsed.total_seconds() < COOLDOWN_SECONDS

def get_cooldown_remaining():
    """Get the remaining cooldown time in seconds"""
    if 'last_refresh_dt' not in st.session_state or st.session_state.last_refresh_dt is None:
        return 0
        
    elapsed = datetime.now() - st.session_state.last_refresh_dt
    remaining = COOLDOWN_SECONDS - elapsed.total_seconds()
    return max(0, remaining)

def sync_with_backend_refresh_time():
    """
    Sync the local cooldown timer with the backend's data refresh time.
    This is useful when the page is refreshed to ensure the cooldown
    timer displays the correct remaining time.
    """
    if 'last_refresh_dt' not in st.session_state:
        return
        
    try:
        # Get health status from backend
        response = requests.get(build_api_url("/health"))
        if response.status_code == 200:
            health_data = response.json()
            if 'latest_props' in health_data and 'age_minutes' in health_data['latest_props']:
                # Backend's props age in minutes
                backend_age_minutes = health_data['latest_props']['age_minutes'] or 0
                
                # Calculate the earliest refresh time
                current_time = datetime.now()
                backend_refresh_time = current_time - timedelta(minutes=backend_age_minutes)
                
                # Update local refresh time if backend data is newer
                if backend_refresh_time > st.session_state.last_refresh_dt:
                    st.session_state.last_refresh_dt = backend_refresh_time
                    st.session_state.last_refresh = backend_refresh_time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Update cache
                    if 'cache_data' in st.session_state:
                        st.session_state.cache_data['last_refresh'] = st.session_state.last_refresh
                        
    except Exception as e:
        print(f"Error syncing with backend: {e}")

def main():
    st.set_page_config(
        page_title="Sports Betting Model",
        page_icon="🏀",
        layout="wide"
    )
    
    st.title("🏀 Sports Betting Model")
    st.markdown("Find value plays across different bookmakers")
    
    # Add information about current limitations and future plans
    st.info("ℹ️ **Note:** This tool currently fetches upcoming NBA games for the next 24 hours only. Future versions will allow selecting specific dates and times.")
    
    # Display API connection status
    api_status = check_api_connection()
    if api_status:
        st.success(f"✅ Connected to API: {API_URL}")
    else:
        st.error(f"❌ Cannot connect to API: {API_URL}")
        st.warning("Please check the API URL configuration or ensure the API server is running.")
    
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
        
        # Initialize cache_data if not present
        if 'cache_data' not in st.session_state:
            st.session_state.cache_data = {}
            
        st.session_state.initialized = True
        
        # Sync with backend after initialization
        sync_with_backend_refresh_time()
    
    # Define callback for bookmaker selection change
    def on_bookmaker_change():
        if st.session_state.selected_bookmaker != st.session_state.previous_selected_bookmaker:
            st.session_state.is_switching_bookmakers = True
            st.session_state.current_bookmaker = st.session_state.selected_bookmaker  # Update current_bookmaker
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # Sportsbook selection with popular options at top
        bookmaker_options = DEFAULT_BOOKMAKERS + [b for b in sorted(SPORTSBOOKS) if b not in DEFAULT_BOOKMAKERS]
        
        # If we're in cooldown but changing bookmaker, handle differently
        previous_bookmaker = st.session_state.get('previous_selected_bookmaker')
        
        # Sportsbook selection - using on_change callback
        selected_bookmaker = st.selectbox(
            "Select Sportsbook",
            bookmaker_options,
            format_func=lambda x: x.capitalize(),
            index=bookmaker_options.index(previous_bookmaker) if previous_bookmaker in bookmaker_options else 0,
            key="selected_bookmaker",
            on_change=on_bookmaker_change
        )
        
        # Minimum edge slider
        min_edge = st.slider(
            "Minimum Edge (%)",
            min_value=0.0,
            max_value=10.0,
            value=2.0,
            step=0.5,
            key="min_edge"
        )
        
        # Handle bookmaker change process in main flow
        if st.session_state.is_switching_bookmakers:
            # Show loading message when switching bookmakers
            with st.spinner(f"🔄 Switching to {selected_bookmaker.capitalize()}..."):
                # Process the bookmaker change
                get_value_plays(selected_bookmaker, min_edge, force_local=True)
                
                # Update tracking state
                st.session_state.previous_selected_bookmaker = selected_bookmaker
                st.session_state.is_switching_bookmakers = False
                
                # Force rerun to update UI immediately
                st.rerun()
        
        # Get props button with cooldown
        cooldown_active = button_cooldown_active()
        cooldown_remaining = get_cooldown_remaining()
        
        # Sync with backend for accurate cooldown timing
        if 'initialized' in st.session_state and 'last_refresh_dt' in st.session_state:
            sync_with_backend_refresh_time()
            # Recalculate cooldown after syncing
            cooldown_active = button_cooldown_active()
            cooldown_remaining = get_cooldown_remaining()
        
        if cooldown_active:
            remaining_mins = int(cooldown_remaining // 60)
            remaining_secs = int(cooldown_remaining % 60)
            st.warning(f"⏳ Please wait {remaining_mins}m {remaining_secs}s before refreshing")
            
            # The button exists but is disabled
            refresh_button = st.button("Get Fresh Props", disabled=True, key="refresh_disabled")
            
            # Add a note about switching bookmakers
            st.caption("You can switch bookmakers while waiting by selecting a different option above")
        else:
            # Only show button when not in middle of switching bookmakers
            refresh_button = st.button("Get Fresh Props", key="refresh_enabled")
            if refresh_button:
                with st.spinner("Fetching props data..."):
                    get_value_plays(selected_bookmaker, min_edge)
        
        # Add statistics in the sidebar
        if st.session_state.value_plays and st.session_state.value_plays.get('stats'):
            st.divider()
            st.subheader("📊 Statistics")
            stats = st.session_state.value_plays.get('stats', {})
            if stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Avg Edge", f"{stats.get('avg_edge', 0):.2f}%")
                    st.metric("Avg EV", f"{stats.get('avg_ev', 0):.2f}%")
                with col2:
                    st.metric("Max Edge", f"{stats.get('max_edge', 0):.2f}%")
                    st.metric("Max EV", f"{stats.get('max_ev', 0):.2f}%")
    
    # Main content area - use full width for the value plays
    st.header("Value Plays")
    current_bookmaker = st.session_state.get('current_bookmaker', None)
    
    # Always sync with backend when displaying cooldown timer
    if 'initialized' in st.session_state and 'last_refresh_dt' in st.session_state:
        sync_with_backend_refresh_time()
    
    if current_bookmaker:
        st.subheader(f"Results for {current_bookmaker.capitalize()}")
        
    if st.session_state.value_plays:
        result_container = st.container()
        with result_container:
            # Status information in a horizontal layout
            status_col1, status_col2, status_col3 = st.columns([1, 2, 1])
            with status_col1:
                st.success(f"Found {st.session_state.value_plays['total_plays']} value plays!")
            with status_col2:
                if st.session_state.last_refresh:
                    st.caption(f"Last refreshed: {st.session_state.last_refresh}")
            with status_col3:
                # Auto-refresh countdown
                if cooldown_active:
                    # Recalculate cooldown remaining after syncing
                    cooldown_remaining = get_cooldown_remaining()
                    st.caption(f"Next refresh available in: {int(cooldown_remaining // 60)}m {int(cooldown_remaining % 60)}s")
        
        # Display value plays with full width
        display_value_plays(st.session_state.value_plays)
    else:
        st.info("Select a sportsbook and click 'Get Props' to see results")

def check_api_connection():
    """Check if the API is accessible"""
    try:
        response = requests.get(build_api_url('/'), timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"API connection error: {str(e)}")
        return False

def get_value_plays(bookmaker: str, min_edge: float, force_local: bool = False):
    """
    Get value plays for the selected bookmaker
    
    Args:
        bookmaker: Name of the bookmaker to analyze
        min_edge: Minimum edge percentage to consider
        force_local: Force using locally cached data without API refresh
    """
    try:
        is_switching = force_local and bookmaker != st.session_state.get('previous_selected_bookmaker')
        
        if is_switching:
            # Log when we're switching bookmakers
            print(f"Switching from {st.session_state.get('previous_selected_bookmaker', 'None')} to {bookmaker}")
            st.info(f"Analyzing data for {bookmaker.capitalize()}...")
        
        # Update session state immediately to reflect the current selection
        st.session_state.current_bookmaker = bookmaker
        
        # For bookmaker switches during cooldown, use the latest props file without refreshing
        if force_local and 'last_props_data_time' in st.session_state:
            print(f"Using locally cached props data for {bookmaker}")
            
            # Get props dataframe from session state
            if 'raw_props_df' in st.session_state and not st.session_state.raw_props_df.empty:
                raw_props_df = st.session_state.raw_props_df
                
                # Find value plays using compare_bookmakers
                response = requests.post(
                    build_api_url(f"/value-plays/{bookmaker}"),
                    params={"min_edge": min_edge},
                    json={"use_cached": True}
                )
                
                if response.status_code != 200:
                    # For Streamlit Cloud, we won't have local calculation fallback since we 
                    # don't have direct access to the comparison module
                    st.error(f"Error analyzing data for {bookmaker}: API returned status {response.status_code}")
                    return
                else:
                    # Update display values but keep the last refresh time from the original props fetch
                    st.session_state.value_plays = response.json()
                    
                    # Save to cache with updated bookmaker
                    cache_data = {
                        'value_plays': st.session_state.value_plays,
                        'last_refresh': st.session_state.last_refresh,
                        'selected_bookmaker': bookmaker,
                        'current_bookmaker': bookmaker,
                        'previous_selected_bookmaker': bookmaker
                    }
                    save_cache_data(cache_data)
                    
                    if is_switching:
                        st.success(f"Switched to {bookmaker.capitalize()} successfully!")
                    
                    return
            
            # If we don't have the raw data locally, try getting latest file path from API
            response = requests.get(build_api_url("/latest-props-file"))
            if response.status_code == 200:
                file_info = response.json()
                
                # Now get value plays for the new bookmaker using the existing file
                response = requests.get(
                    build_api_url(f"/value-plays/{bookmaker}"),
                    params={"min_edge": min_edge}
                )
                
                if response.status_code == 200:
                    # Update session state but keep original refresh time
                    st.session_state.value_plays = response.json()
                    
                    # Save to cache with updated bookmaker
                    cache_data = {
                        'value_plays': st.session_state.value_plays,
                        'last_refresh': st.session_state.last_refresh,
                        'selected_bookmaker': bookmaker,
                        'current_bookmaker': bookmaker,
                        'previous_selected_bookmaker': bookmaker
                    }
                    save_cache_data(cache_data)
                    
                    if is_switching:
                        st.success(f"Switched to {bookmaker.capitalize()} successfully!")
                    
                    return
            
            # If we couldn't use local data, fall back to regular API call
        
        # Regular API call for initial or refreshed data
        value_plays_url = build_api_url(f"/value-plays/{bookmaker}")
        print(f"Requesting value plays from: {value_plays_url}")
        
        response = requests.get(
            value_plays_url,
            params={"min_edge": min_edge}
        )
        
        if response.status_code == 200:
            # Update session state
            current_time = datetime.now()
            st.session_state.value_plays = response.json()
            st.session_state.last_refresh = current_time.strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.last_refresh_dt = current_time
            st.session_state.last_props_data_time = current_time
            
            # Get the backend's refresh time from health endpoint to sync
            try:
                health_response = requests.get(build_api_url("/health"))
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    if 'latest_props' in health_data and 'age_minutes' in health_data['latest_props']:
                        # The backend's props data age is in minutes, convert back to a datetime
                        backend_age_minutes = health_data['latest_props']['age_minutes'] or 0
                        # Calculate the backend's refresh time
                        backend_refresh_time = current_time - timedelta(minutes=backend_age_minutes)
                        # Update our refresh time to match (if newer)
                        if backend_refresh_time > st.session_state.last_refresh_dt:
                            st.session_state.last_refresh_dt = backend_refresh_time
                            st.session_state.last_refresh = backend_refresh_time.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                print(f"Could not sync with backend refresh time: {e}")
            
            # Try to save raw props data to session state by fetching the CSV file
            try:
                latest_file_response = requests.get(build_api_url("/latest-props-file"))
                if latest_file_response.status_code == 200:
                    file_info = latest_file_response.json()
                    # For Streamlit Cloud, we don't save the actual file path since we can't access it
                    st.session_state.latest_props_info = file_info
            except Exception as e:
                print(f"Could not get latest props file: {e}")
            
            # Cache the data - only save JSON serializable values
            cache_data = {
                'value_plays': st.session_state.value_plays,
                'last_refresh': st.session_state.last_refresh,
                'selected_bookmaker': bookmaker,
                'current_bookmaker': bookmaker,
                'previous_selected_bookmaker': bookmaker
            }
            save_cache_data(cache_data)
            
            st.success(f"Found {st.session_state.value_plays['total_plays']} value plays!")
        else:
            st.error(f"Error getting value plays: {response.text}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        print(f"Detailed API error: {str(e)}")

def display_value_plays(value_plays: dict):
    """Display the value plays in a nice format"""
    if not value_plays["plays"]:
        st.info("No value plays found for the selected criteria")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(value_plays["plays"])
    
    # Format columns
    if 'target_odds' in df.columns:
        df['target_odds'] = df['target_odds'].apply(
            lambda x: f"+{int(x)}" if x > 0 else f"{int(x)}"
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
            "edge": "Edge",
            "ev_percentage": "EV",
            "game": "Game",
            "recommendation": "Recommendation"
        },
        hide_index=True
    )
    
    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        "Download CSV",
        csv,
        f"value_plays_{value_plays['bookmaker']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv"
    )

if __name__ == "__main__":
    main() 