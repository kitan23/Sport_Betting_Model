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

# Constants
API_URL = "http://localhost:8000"
COOLDOWN_SECONDS = 300  # 5 minutes
CACHE_FILE = "streamlit_cache.json"

# Available sportsbooks
SPORTSBOOKS = ["Fanatics", "FanDuel", "DraftKings"]

def load_cached_data():
    """Load cached data from file if it exists"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                
                # Convert timestamp string back to datetime
                if 'last_refresh' in data and data['last_refresh']:
                    data['last_refresh_dt'] = datetime.strptime(data['last_refresh'], "%Y-%m-%d %H:%M:%S")
                return data
        except Exception as e:
            st.error(f"Error loading cached data: {e}")
    return {}

def save_cache_data(data):
    """Save data to cache file"""
    try:
        # Create a copy of the data to avoid modifying the original
        cache_data = data.copy()
        
        # Convert datetime objects to strings
        if 'last_refresh_dt' in cache_data:
            del cache_data['last_refresh_dt']  # Remove the datetime object
            
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
    
    # Load cached data on initial load
    if 'initialized' not in st.session_state:
        cached_data = load_cached_data()
        
        # Initialize session state with cached data
        st.session_state.last_refresh = cached_data.get('last_refresh')
        st.session_state.last_refresh_dt = cached_data.get('last_refresh_dt')
        st.session_state.value_plays = cached_data.get('value_plays')
        st.session_state.initialized = True
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # Sportsbook selection
        selected_bookmaker = st.selectbox(
            "Select Sportsbook",
            SPORTSBOOKS
        )
        
        # Minimum edge slider
        min_edge = st.slider(
            "Minimum Edge (%)",
            min_value=0.0,
            max_value=10.0,
            value=2.0,
            step=0.5
        )
        
        # Get props button with cooldown
        cooldown_active = button_cooldown_active()
        cooldown_remaining = get_cooldown_remaining()
        
        if cooldown_active:
            remaining_mins = int(cooldown_remaining // 60)
            remaining_secs = int(cooldown_remaining % 60)
            st.warning(f"⏳ Please wait {remaining_mins}m {remaining_secs}s before refreshing")
            st.button("Get Props", disabled=True)
        else:
            if st.button("Get Props"):
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
                    st.caption(f"Next refresh available in: {int(cooldown_remaining // 60)}m {int(cooldown_remaining % 60)}s")
        
        # Display value plays with full width
        display_value_plays(st.session_state.value_plays)
    else:
        st.info("Select a sportsbook and click 'Get Props' to see results")

def get_value_plays(bookmaker: str, min_edge: float):
    """Get value plays for the selected bookmaker"""
    try:
        response = requests.get(
            f"{API_URL}/value-plays/{bookmaker}",
            params={"min_edge": min_edge}
        )
        
        if response.status_code == 200:
            # Update session state
            current_time = datetime.now()
            st.session_state.value_plays = response.json()
            st.session_state.last_refresh = current_time.strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.last_refresh_dt = current_time
            
            # Cache the data - only save JSON serializable values
            cache_data = {
                'value_plays': st.session_state.value_plays,
                'last_refresh': st.session_state.last_refresh
                # Don't include last_refresh_dt as it's not JSON serializable
            }
            save_cache_data(cache_data)
            
            st.success(f"Found {st.session_state.value_plays['total_plays']} value plays!")
        else:
            st.error(f"Error getting value plays: {response.text}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")

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