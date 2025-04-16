"""
Sports Betting Model - Statistics Calculation Module

This module contains functions to perform various calculations for sports betting analysis,
including implied probability, expected value (EV), median lines, fair lines, and devigging.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
import json
import re
import os
from datetime import datetime

def convert_american_to_decimal(american_odds: float) -> float:
    """
    Convert American odds to decimal odds.
    
    Args:
        american_odds: The American odds value
        
    Returns:
        Decimal odds equivalent
    """
    if pd.isnull(american_odds):
        return None
    
    american_odds = float(american_odds)
    if american_odds > 0:
        return round((american_odds / 100) + 1, 4)
    else:
        return round((100 / abs(american_odds)) + 1, 4)

def convert_decimal_to_american(decimal_odds: float) -> int:
    """
    Convert decimal odds to American odds.
    
    Args:
        decimal_odds: The decimal odds value
        
    Returns:
        American odds equivalent
    """
    if pd.isnull(decimal_odds) or decimal_odds <= 1:
        return None
    
    if decimal_odds >= 2:
        return int(round((decimal_odds - 1) * 100))
    else:
        return int(round(-100 / (decimal_odds - 1)))

def calculate_implied_probability(decimal_odds: float) -> float:
    """
    Calculate implied probability from decimal odds.
    
    Args:
        decimal_odds: The decimal odds value
        
    Returns:
        Implied probability (0-1)
    """
    if pd.isnull(decimal_odds) or decimal_odds <= 0:
        return None
    
    return round(1 / decimal_odds, 4)

def calculate_no_vig_probability(over_prob: float, under_prob: float) -> Tuple[float, float]:
    """
    Calculate no-vig probabilities for over/under markets.
    
    Args:
        over_prob: Implied probability for the over
        under_prob: Implied probability for the under
        
    Returns:
        Tuple of (no_vig_over_prob, no_vig_under_prob)
    """
    if pd.isnull(over_prob) or pd.isnull(under_prob):
        return (None, None)
    
    # Calculate the overround (total probability)
    total_prob = over_prob + under_prob
    
    # Remove the vig by normalizing the probabilities
    no_vig_over = round(over_prob / total_prob, 4)
    no_vig_under = round(under_prob / total_prob, 4)
    
    return (no_vig_over, no_vig_under)

def calculate_no_vig_odds(over_odds: float, under_odds: float) -> Tuple[float, float]:
    """
    Calculate no-vig odds for over/under markets.
    
    Args:
        over_odds: American odds for the over
        under_odds: American odds for the under
        
    Returns:
        Tuple of (no_vig_over_odds, no_vig_under_odds) in American odds format
    """
    # Convert to decimal odds
    over_decimal = convert_american_to_decimal(over_odds)
    under_decimal = convert_american_to_decimal(under_odds)
    
    # Calculate implied probabilities
    over_prob = calculate_implied_probability(over_decimal)
    under_prob = calculate_implied_probability(under_decimal)
    
    # Calculate no-vig probabilities
    no_vig_over_prob, no_vig_under_prob = calculate_no_vig_probability(over_prob, under_prob)
    
    # Convert back to decimal odds
    no_vig_over_decimal = 1 / no_vig_over_prob if no_vig_over_prob else None
    no_vig_under_decimal = 1 / no_vig_under_prob if no_vig_under_prob else None
    
    # Convert to American odds
    no_vig_over_american = convert_decimal_to_american(no_vig_over_decimal)
    no_vig_under_american = convert_decimal_to_american(no_vig_under_decimal)
    
    return (no_vig_over_american, no_vig_under_american)

def calculate_ev(bet_odds: float, true_probability: float, stake: float = 100) -> float:
    """
    Calculate the expected value (EV) of a bet.
    
    Args:
        bet_odds: The decimal odds of the bet
        true_probability: The true probability of the outcome (0-1)
        stake: The amount being wagered (default: 100)
        
    Returns:
        Expected value of the bet
    """
    if pd.isnull(bet_odds) or pd.isnull(true_probability):
        return None
    
    # Calculate potential profit
    potential_profit = stake * (bet_odds - 1)
    
    # Calculate EV
    ev = (true_probability * potential_profit) - ((1 - true_probability) * stake)
    
    # Return as percentage
    return round((ev / stake) * 100, 2)

def extract_bookmaker_odds(bookmaker_data: str) -> Dict[str, Dict]:
    """
    Extract bookmaker odds from the JSON string in the CSV.
    
    Args:
        bookmaker_data: JSON string containing bookmaker data
        
    Returns:
        Dictionary of bookmaker odds
    """
    if pd.isnull(bookmaker_data) or bookmaker_data == "":
        return {}
    
    try:
        # Clean the string if needed (sometimes CSV can have formatting issues)
        cleaned_data = re.sub(r"'", '"', bookmaker_data)
        bookmakers = json.loads(cleaned_data)
        return bookmakers
    except (json.JSONDecodeError, TypeError):
        # Try to parse it as a string representation of a dict
        try:
            # This is a fallback method if the JSON parsing fails
            bookmakers = eval(bookmaker_data)
            return bookmakers
        except:
            return {}

def get_median_line(props_df: pd.DataFrame, prop_type: str, player_name: str) -> float:
    """
    Get the median line (over/under value) across all bookmakers for a specific player and prop type.
    
    Args:
        props_df: DataFrame containing player props data
        prop_type: Type of prop (e.g., 'points', 'rebounds', etc.)
        player_name: Name of the player
        
    Returns:
        Median line value
    """
    # Filter for the specific player and prop type
    player_props = props_df[(props_df['player_name'] == player_name) & 
                           (props_df['prop_type'] == prop_type)]
    
    if player_props.empty:
        return None
    
    # Extract all lines from bookmakers
    all_lines = []
    
    for _, row in player_props.iterrows():
        # Get the bookOverUnder value
        if not pd.isnull(row.get('bookOverUnder')):
            all_lines.append(float(row['bookOverUnder']))
        
        # Extract lines from individual bookmakers
        bookmaker_data = row.get('byBookmaker')
        if not pd.isnull(bookmaker_data):
            bookmakers = extract_bookmaker_odds(bookmaker_data)
            for bookie, data in bookmakers.items():
                if 'overUnder' in data and data.get('available', False):
                    try:
                        line = float(data['overUnder'])
                        all_lines.append(line)
                    except (ValueError, TypeError):
                        continue
    
    # Return the median if we have lines
    if all_lines:
        return np.median(all_lines)
    else:
        return None

def get_fair_line(props_df: pd.DataFrame, prop_type: str, player_name: str) -> float:
    """
    Get the fair line from the API if available.
    
    Args:
        props_df: DataFrame containing player props data
        prop_type: Type of prop (e.g., 'points', 'rebounds', etc.)
        player_name: Name of the player
        
    Returns:
        Fair line value
    """
    # Filter for the specific player and prop type
    player_props = props_df[(props_df['player_name'] == player_name) & 
                           (props_df['prop_type'] == prop_type)]
    
    if player_props.empty:
        return None
    
    # Check if fairOverUnder is available
    fair_lines = player_props['fairOverUnder'].dropna()
    
    if not fair_lines.empty:
        # Return the first fair line (they should all be the same)
        return float(fair_lines.iloc[0])
    else:
        return None

def calculate_closing_line_value(bet_odds: float, closing_odds: float) -> float:
    """
    Calculate Closing Line Value (CLV) - the difference between the odds you bet at and the closing odds.
    
    Args:
        bet_odds: The American odds you bet at
        closing_odds: The American odds at closing
        
    Returns:
        CLV as a percentage
    """
    if pd.isnull(bet_odds) or pd.isnull(closing_odds):
        return None
    
    # Convert to decimal
    bet_decimal = convert_american_to_decimal(bet_odds)
    closing_decimal = convert_american_to_decimal(closing_odds)
    
    # Calculate CLV
    if bet_decimal > closing_decimal:
        # Positive CLV
        clv = ((bet_decimal / closing_decimal) - 1) * 100
    else:
        # Negative CLV
        clv = -((closing_decimal / bet_decimal) - 1) * 100
    
    return round(clv, 2)

def find_best_odds(props_df: pd.DataFrame, prop_type: str, player_name: str, direction: str = 'over') -> Dict:
    """
    Find the best available odds for a specific player, prop type, and direction.
    
    Args:
        props_df: DataFrame containing player props data
        prop_type: Type of prop (e.g., 'points', 'rebounds', etc.)
        player_name: Name of the player
        direction: 'over' or 'under'
        
    Returns:
        Dictionary with best odds information
    """
    # Filter for the specific player, prop type, and direction
    player_props = props_df[(props_df['player_name'] == player_name) & 
                           (props_df['prop_type'] == prop_type) &
                           (props_df['direction'] == direction)]
    
    if player_props.empty:
        return None
    
    best_odds = {
        'american_odds': None,
        'decimal_odds': None,
        'bookmaker': None,
        'line': None
    }
    
    # Initialize with a very low value for comparison
    best_decimal = 0
    
    for _, row in player_props.iterrows():
        bookmaker_data = row.get('byBookmaker')
        if pd.isnull(bookmaker_data):
            continue
            
        bookmakers = extract_bookmaker_odds(bookmaker_data)
        
        for bookie, data in bookmakers.items():
            if not data.get('available', False):
                continue
                
            try:
                american = float(data['odds'])
                decimal = convert_american_to_decimal(american)
                line = float(data['overUnder'])
                
                # Check if these odds are better
                if decimal > best_decimal:
                    best_decimal = decimal
                    best_odds['american_odds'] = american
                    best_odds['decimal_odds'] = decimal
                    best_odds['bookmaker'] = bookie
                    best_odds['line'] = line
            except (ValueError, TypeError, KeyError):
                continue
    
    return best_odds

def find_median_odds(props_df: pd.DataFrame, prop_type: str, player_name: str, direction: str = 'over') -> Dict:
    """
    Find the median odds across all bookmakers for a specific player prop and direction.
    
    Args:
        props_df: DataFrame containing player props data
        prop_type: Type of prop (e.g., 'points', 'rebounds', etc.)
        player_name: Name of the player
        direction: 'over' or 'under'
        
    Returns:
        Dictionary with median odds information or None if no valid odds
    """
    # Filter for the specific player, prop type, and direction
    player_props = props_df[(props_df['player_name'] == player_name) & 
                           (props_df['prop_type'] == prop_type) &
                           (props_df['direction'] == direction)]
    
    if player_props.empty:
        return None
    
    # Get the first row (should only be one row per player/prop/direction)
    row = player_props.iloc[0]
    
    # Get bookmaker data
    bookmaker_data = row.get('byBookmaker')
    if pd.isnull(bookmaker_data):
        return None
    
    # Get median odds
    return get_median_odds(bookmaker_data, direction)

def analyze_player_prop(props_df: pd.DataFrame, prop_type: str, player_name: str) -> Dict:
    """
    Perform comprehensive analysis on a player prop.
    
    Args:
        props_df: DataFrame containing player props data
        prop_type: Type of prop (e.g., 'points', 'rebounds', etc.)
        player_name: Name of the player
        
    Returns:
        Dictionary with analysis results
    """
    # Get the fair line if available
    fair_line = get_fair_line(props_df, prop_type, player_name)
    
    # If no fair line, use median line
    if fair_line is None:
        fair_line = get_median_line(props_df, prop_type, player_name)
    
    if fair_line is None:
        return {
            'player': player_name,
            'prop_type': prop_type,
            'error': 'No line data available'
        }
    
    # Find median odds for over and under (instead of best odds)
    median_over = find_median_odds(props_df, prop_type, player_name, 'over')
    median_under = find_median_odds(props_df, prop_type, player_name, 'under')
    
    # Filter for the specific player and prop type to get fair odds
    player_props = props_df[(props_df['player_name'] == player_name) & 
                           (props_df['prop_type'] == prop_type)]
    
    # Get fair odds if available
    fair_over_odds = None
    fair_under_odds = None
    
    if not player_props.empty:
        over_row = player_props[player_props['direction'] == 'over']
        under_row = player_props[player_props['direction'] == 'under']
        
        if not over_row.empty and not pd.isnull(over_row.iloc[0].get('fairOdds')):
            fair_over_odds = float(over_row.iloc[0]['fairOdds'])
        
        if not under_row.empty and not pd.isnull(under_row.iloc[0].get('fairOdds')):
            fair_under_odds = float(under_row.iloc[0]['fairOdds'])
    
    # If no fair odds, calculate no-vig odds
    if fair_over_odds is None or fair_under_odds is None:
        if median_over and median_under:
            fair_over_odds, fair_under_odds = calculate_no_vig_odds(
                median_over['american_odds'], 
                median_under['american_odds']
            )
    
    # Calculate implied probabilities
    over_implied_prob = None
    under_implied_prob = None
    
    if median_over:
        over_implied_prob = calculate_implied_probability(median_over['decimal_odds'])
    
    if median_under:
        under_implied_prob = calculate_implied_probability(median_under['decimal_odds'])
    
    # Calculate fair probabilities
    fair_over_prob = None
    fair_under_prob = None
    
    if fair_over_odds:
        fair_over_decimal = convert_american_to_decimal(fair_over_odds)
        fair_over_prob = calculate_implied_probability(fair_over_decimal)
    
    if fair_under_odds:
        fair_under_decimal = convert_american_to_decimal(fair_under_odds)
        fair_under_prob = calculate_implied_probability(fair_under_decimal)
    
    # Calculate EV
    over_ev = None
    under_ev = None
    
    if over_implied_prob and fair_over_prob:
        over_decimal = median_over['decimal_odds'] if median_over else None
        if over_decimal:
            over_ev = calculate_ev(over_decimal, fair_over_prob)
    
    if under_implied_prob and fair_under_prob:
        under_decimal = median_under['decimal_odds'] if median_under else None
        if under_decimal:
            under_ev = calculate_ev(under_decimal, fair_under_prob)
    
    # Count bookmakers
    over_bookmaker_count = over_row['over_bookmaker_count'].max() if 'over_bookmaker_count' in over_row.columns else 0
    under_bookmaker_count = under_row['under_bookmaker_count'].max() if 'under_bookmaker_count' in under_row.columns else 0
    total_bookmaker_count = over_row['bookmaker_count'].max() if 'bookmaker_count' in over_row.columns else 0
    
    # If bookmaker counts are still zero, try to calculate them directly
    if over_bookmaker_count == 0 and 'byBookmaker' in over_row.columns and not over_row.empty:
        over_bookmaker_count = count_available_bookmakers(over_row['byBookmaker'].iloc[0], 'over')
        
    if under_bookmaker_count == 0 and 'byBookmaker' in under_row.columns and not under_row.empty:
        under_bookmaker_count = count_available_bookmakers(under_row['byBookmaker'].iloc[0], 'under')
        
    if total_bookmaker_count == 0 and 'byBookmaker' in over_row.columns and not over_row.empty:
        total_bookmaker_count = count_available_bookmakers(over_row['byBookmaker'].iloc[0])
    
    # Compile results
    return {
        'player': player_name,
        'prop_type': prop_type,
        'fair_line': fair_line,
        'over': {
            'median_odds': median_over,  # Renamed from best_odds to median_odds
            'fair_odds': fair_over_odds,
            'implied_probability': over_implied_prob,
            'fair_probability': fair_over_prob,
            'ev': over_ev
        },
        'under': {
            'median_odds': median_under,  # Renamed from best_odds to median_odds
            'fair_odds': fair_under_odds,
            'implied_probability': under_implied_prob,
            'fair_probability': fair_under_prob,
            'ev': under_ev
        },
        'over_bookmaker_count': over_bookmaker_count,
        'under_bookmaker_count': under_bookmaker_count,
        'total_bookmaker_count': total_bookmaker_count
    }

def find_value_bets(props_df: pd.DataFrame, min_ev: float = 3.0) -> pd.DataFrame:
    """
    Find all value bets with EV above the minimum threshold.
    
    Args:
        props_df: DataFrame containing player props data
        min_ev: Minimum EV percentage to consider a value bet
        
    Returns:
        DataFrame with value bets
    """
    # Get unique player and prop type combinations
    player_props = props_df[['player_name', 'prop_type']].drop_duplicates()
    
    value_bets = []
    
    for _, row in player_props.iterrows():
        player = row['player_name']
        prop_type = row['prop_type']
        
        # Analyze this prop
        analysis = analyze_player_prop(props_df, prop_type, player)
        
        # Check if over is a value bet
        if 'over' in analysis and analysis['over'].get('ev') and analysis['over']['ev'] >= min_ev:
            value_bets.append({
                'player': player,
                'prop_type': prop_type,
                'direction': 'over',
                'line': analysis['fair_line'],
                'bookmaker': analysis['over']['median_odds']['bookmaker'] if analysis['over']['median_odds'] else None,
                'odds': analysis['over']['median_odds']['american_odds'] if analysis['over']['median_odds'] else None,
                'fair_odds': analysis['over']['fair_odds'],
                'ev': analysis['over']['ev']
            })
        
        # Check if under is a value bet
        if 'under' in analysis and analysis['under'].get('ev') and analysis['under']['ev'] >= min_ev:
            value_bets.append({
                'player': player,
                'prop_type': prop_type,
                'direction': 'under',
                'line': analysis['fair_line'],
                'bookmaker': analysis['under']['median_odds']['bookmaker'] if analysis['under']['median_odds'] else None,
                'odds': analysis['under']['median_odds']['american_odds'] if analysis['under']['median_odds'] else None,
                'fair_odds': analysis['under']['fair_odds'],
                'ev': analysis['under']['ev']
            })
    
    # Convert to DataFrame and sort by EV
    if value_bets:
        value_df = pd.DataFrame(value_bets)
        return value_df.sort_values('ev', ascending=False)
    else:
        return pd.DataFrame()

def process_props_data(csv_file: str) -> pd.DataFrame:
    """
    Process the player props CSV file and add calculated statistics.
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        DataFrame with processed data
    """
    # Read the CSV file
    props_df = pd.read_csv(csv_file)
    
    # Convert American odds to decimal
    if 'bookOdds' in props_df.columns:
        props_df['decimal_odds'] = props_df['bookOdds'].apply(convert_american_to_decimal)
    
    # Calculate implied probability
    if 'decimal_odds' in props_df.columns:
        props_df['implied_probability'] = props_df['decimal_odds'].apply(calculate_implied_probability)
    
    # Calculate no-vig probabilities for each market
    markets = props_df[['oddID', 'opposingOddID', 'prop_type', 'player_name', 'direction', 'implied_probability']]
    
    # Create a dictionary to store no-vig probabilities
    no_vig_probs = {}
    
    for _, row in markets.iterrows():
        if row['direction'] == 'over':
            # Find the corresponding under market
            under_market = markets[(markets['player_name'] == row['player_name']) & 
                                  (markets['prop_type'] == row['prop_type']) & 
                                  (markets['direction'] == 'under')]
            
            if not under_market.empty:
                over_prob = row['implied_probability']
                under_prob = under_market.iloc[0]['implied_probability']
                
                if not pd.isnull(over_prob) and not pd.isnull(under_prob):
                    no_vig_over, no_vig_under = calculate_no_vig_probability(over_prob, under_prob)
                    
                    # Store the no-vig probabilities
                    no_vig_probs[row['oddID']] = no_vig_over
                    no_vig_probs[under_market.iloc[0]['oddID']] = no_vig_under
    
    # Add no-vig probabilities to the DataFrame
    props_df['no_vig_probability'] = props_df['oddID'].map(no_vig_probs)
    
    # Calculate no-vig decimal odds
    props_df['no_vig_decimal_odds'] = props_df['no_vig_probability'].apply(
        lambda x: 1/x if not pd.isnull(x) and x > 0 else None
    )
    
    # Calculate no-vig American odds
    props_df['no_vig_american_odds'] = props_df['no_vig_decimal_odds'].apply(convert_decimal_to_american)
    
    return props_df

def count_available_bookmakers(bookmaker_data: str, direction: str = None) -> int:
    """
    Count the number of bookmakers that have this prop available.
    
    Args:
        bookmaker_data: JSON string containing bookmaker data
        direction: Optional direction ('over' or 'under') to count specific bookmakers
        
    Returns:
        Number of available bookmakers
    """
    if pd.isnull(bookmaker_data) or bookmaker_data == "":
        return 0
    
    bookmakers = extract_bookmaker_odds(bookmaker_data)
    
    if direction is None:
        # Count all available bookmakers
        available_count = sum(1 for _, data in bookmakers.items() if data.get('available', False))
    else:
        # Count bookmakers that have the specific direction available
        available_count = 0
        for _, data in bookmakers.items():
            if not data.get('available', False):
                continue
            
            # If we're here, the bookmaker is available
            # For the specific direction, we just need to check if the bookmaker has odds for this direction
            available_count += 1
    
    return available_count

def export_stats_to_csv(props_df: pd.DataFrame, output_file: str = None) -> str:
    """
    Export all calculated statistics to a CSV file, including bookmaker coverage information.
    
    Args:
        props_df: DataFrame containing processed player props data
        output_file: Path to the output CSV file (if None, a default name will be generated)
        
    Returns:
        Path to the created CSV file
    """
    # Create a copy of the DataFrame to avoid modifying the original
    export_df = props_df.copy()
    
    # Count available bookmakers for each prop
    if 'byBookmaker' in export_df.columns:
        # Total bookmakers count
        export_df['bookmaker_count'] = export_df['byBookmaker'].apply(count_available_bookmakers)
        
        # Over bookmakers count
        export_df['over_bookmaker_count'] = export_df['byBookmaker'].apply(
            lambda x: count_available_bookmakers(x, 'over')
        )
        
        # Under bookmakers count
        export_df['under_bookmaker_count'] = export_df['byBookmaker'].apply(
            lambda x: count_available_bookmakers(x, 'under')
        )
        
        # Print some debug information
        print("\nBookmaker count summary:")
        print(f"Total props: {len(export_df)}")
        print(f"Props with bookmakers: {(export_df['bookmaker_count'] > 0).sum()}")
        print(f"Props with over bookmakers: {(export_df['over_bookmaker_count'] > 0).sum()}")
        print(f"Props with under bookmakers: {(export_df['under_bookmaker_count'] > 0).sum()}")
        
        # Sample a few rows to verify
        sample_rows = min(5, len(export_df))
        if sample_rows > 0:
            print("\nSample bookmaker counts:")
            for _, row in export_df.head(sample_rows).iterrows():
                print(f"{row.get('player_name', 'Unknown')} - {row.get('prop_type', 'Unknown')}: " 
                      f"Total={row.get('bookmaker_count', 0)}, "
                      f"Over={row.get('over_bookmaker_count', 0)}, "
                      f"Under={row.get('under_bookmaker_count', 0)}")
    
    # Get unique player and prop type combinations
    player_props = export_df[['player_name', 'prop_type']].drop_duplicates()
    
    # Create a list to store the enhanced stats
    enhanced_stats = []
    
    for _, row in player_props.iterrows():
        player = row['player_name']
        prop_type = row['prop_type']
        
        # Get the player prop data
        player_prop_data = export_df[(export_df['player_name'] == player) & 
                                    (export_df['prop_type'] == prop_type)]
        
        # Skip if no data
        if player_prop_data.empty:
            continue
        
        # Get over and under rows
        over_row = player_prop_data[player_prop_data['direction'] == 'over']
        under_row = player_prop_data[player_prop_data['direction'] == 'under']
        
        # Skip if missing either over or under
        if over_row.empty or under_row.empty:
            continue
        
        # Get the first row of each for basic data
        over_data = over_row.iloc[0]
        under_data = under_row.iloc[0]
        
        # Get the fair line
        fair_line = get_fair_line(export_df, prop_type, player)
        if fair_line is None:
            fair_line = get_median_line(export_df, prop_type, player)
        
        # Get median odds instead of best odds
        median_over = find_median_odds(export_df, prop_type, player, 'over')
        median_under = find_median_odds(export_df, prop_type, player, 'under')
        
        # Calculate no-vig odds if we have both over and under odds
        no_vig_over_odds = None
        no_vig_under_odds = None
        
        if median_over and median_under:
            no_vig_over_odds, no_vig_under_odds = calculate_no_vig_odds(
                median_over['american_odds'], 
                median_under['american_odds']
            )
        
        # Count bookmakers
        over_bookmaker_count = over_row['over_bookmaker_count'].max() if 'over_bookmaker_count' in over_row.columns else 0
        under_bookmaker_count = under_row['under_bookmaker_count'].max() if 'under_bookmaker_count' in under_row.columns else 0
        total_bookmaker_count = over_row['bookmaker_count'].max() if 'bookmaker_count' in over_row.columns else 0
        
        # If bookmaker counts are still zero, try to calculate them directly
        if over_bookmaker_count == 0 and 'byBookmaker' in over_row.columns and not over_row.empty:
            over_bookmaker_count = count_available_bookmakers(over_row['byBookmaker'].iloc[0], 'over')
            
        if under_bookmaker_count == 0 and 'byBookmaker' in under_row.columns and not under_row.empty:
            under_bookmaker_count = count_available_bookmakers(under_row['byBookmaker'].iloc[0], 'under')
            
        if total_bookmaker_count == 0 and 'byBookmaker' in over_row.columns and not over_row.empty:
            total_bookmaker_count = count_available_bookmakers(over_row['byBookmaker'].iloc[0])
        
        # Calculate implied probabilities
        over_implied_prob = calculate_implied_probability(median_over['decimal_odds']) if median_over else None
        under_implied_prob = calculate_implied_probability(median_under['decimal_odds']) if median_under else None
        
        # Calculate no-vig probabilities
        no_vig_over_prob = None
        no_vig_under_prob = None
        
        if over_implied_prob and under_implied_prob:
            no_vig_over_prob, no_vig_under_prob = calculate_no_vig_probability(over_implied_prob, under_implied_prob)
        
        # Create the enhanced stats entry
        stat_entry = {
            'player': player,
            'prop_type': prop_type,
            'fair_line': fair_line,
            'book_line': over_data.get('bookOverUnder', None),
            'total_bookmakers': total_bookmaker_count,
            'over_bookmakers': over_bookmaker_count,
            'under_bookmakers': under_bookmaker_count,
            'median_over_odds': median_over['american_odds'] if median_over else None,
            'median_over_bookmaker': median_over['bookmaker'] if median_over else None,
            'median_under_odds': median_under['american_odds'] if median_under else None,
            'median_under_bookmaker': median_under['bookmaker'] if median_under else None,
            'no_vig_over_odds': no_vig_over_odds,
            'no_vig_under_odds': no_vig_under_odds,
            'over_implied_prob': over_implied_prob,
            'under_implied_prob': under_implied_prob,
            'no_vig_over_prob': no_vig_over_prob,
            'no_vig_under_prob': no_vig_under_prob,
            'game': over_data.get('game', None),
            'home_team': over_data.get('home_team', None),
            'away_team': over_data.get('away_team', None),
            'event_id': over_data.get('event_id', None)
        }
        
        # Calculate EV if we have no-vig probabilities
        if median_over and no_vig_over_prob and fair_line is not None:
            # Calculate the true probability based on the fair line
            # For the over bet, the true probability is the probability that the player exceeds the line
            # This can be estimated using the no-vig probabilities, but adjusted for the difference
            # between the fair line and the book line
            book_line = over_data.get('bookOverUnder', None)
            
            if book_line is not None:
                # If fair_line > book_line, the true probability of going over is higher than the market implies
                # If fair_line < book_line, the true probability of going over is lower than the market implies
                line_difference = fair_line - book_line
                
                # Check if the line difference is reasonable
                # Typically, line differences greater than 3-4 points are rare and may indicate data issues
                if abs(line_difference) > 4:
                    # Log a warning about the large line difference
                    print(f"Warning: Large line difference detected for {player} {prop_type}: fair_line={fair_line}, book_line={book_line}")
                    # Cap the line difference to prevent unrealistic probability adjustments
                    line_difference = np.sign(line_difference) * min(abs(line_difference), 4)
                
                # Use a balanced adjustment factor: 7.5% per unit difference
                # This is between the original 10% and our conservative 5%
                base_adjustment = line_difference * 0.075  # 7.5% per unit difference
                
                # Apply a moderate confidence factor
                confidence_factor = 0.85  # 85% confidence in our line difference
                probability_adjustment = base_adjustment * confidence_factor
                
                # Calculate the true probability for over
                true_over_prob = no_vig_over_prob + probability_adjustment
                true_over_prob = max(0.15, min(0.85, true_over_prob))  # More balanced clamping between 15% and 85%
                
                # Calculate EV
                ev_value = calculate_ev(
                    median_over['decimal_odds'], 
                    true_over_prob
                )
                
                # Cap extreme EV values
                if ev_value is not None and abs(ev_value) > 100:
                    print(f"Warning: Extreme EV value capped for {player} {prop_type} over: {ev_value}%")
                    ev_value = np.sign(ev_value) * 100
                
                stat_entry['over_ev'] = ev_value
            else:
                stat_entry['over_ev'] = None
        else:
            stat_entry['over_ev'] = None
            
        if median_under and no_vig_under_prob and fair_line is not None:
            # For under bets, the relationship is inverse
            book_line = under_data.get('bookOverUnder', None)
            
            if book_line is not None:
                # If fair_line > book_line, the true probability of going under is lower than the market implies
                # If fair_line < book_line, the true probability of going under is higher than the market implies
                line_difference = fair_line - book_line
                
                # Check if the line difference is reasonable
                if abs(line_difference) > 4:
                    # Log a warning about the large line difference
                    print(f"Warning: Large line difference detected for {player} {prop_type}: fair_line={fair_line}, book_line={book_line}")
                    # Cap the line difference to prevent unrealistic probability adjustments
                    line_difference = np.sign(line_difference) * min(abs(line_difference), 4)
                
                # For under bets, the adjustment is in the opposite direction
                # Use a balanced adjustment factor: 7.5% per unit difference
                base_adjustment = line_difference * 0.075  # 7.5% per unit difference, positive for under
                
                # Apply the same confidence factor for consistency
                confidence_factor = 0.85  # 85% confidence in our line difference
                probability_adjustment = base_adjustment * confidence_factor
                
                # Calculate the true probability for under
                # For UNDER bets:
                # If fair_line > book_line, true probability should be LOWER (subtract adjustment)
                # If fair_line < book_line, true probability should be HIGHER (add adjustment)
                if line_difference > 0:
                    # Fair line > book line: LOWER probability (subtract adjustment)
                    true_under_prob = no_vig_under_prob - probability_adjustment
                elif line_difference < 0:
                    # Fair line < book line: HIGHER probability (add adjustment)
                    true_under_prob = no_vig_under_prob + probability_adjustment
                else:
                    # No difference, use no-vig probability
                    true_under_prob = no_vig_under_prob
                
                true_under_prob = max(0.15, min(0.85, true_under_prob))  # More balanced clamping between 15% and 85%
                
                # Calculate EV
                ev_value = calculate_ev(
                    median_under['decimal_odds'], 
                    true_under_prob
                )
                
                # Cap extreme EV values
                if ev_value is not None and abs(ev_value) > 100:
                    print(f"Warning: Extreme EV value capped for {player} {prop_type} under: {ev_value}%")
                    ev_value = np.sign(ev_value) * 100
                
                stat_entry['under_ev'] = ev_value
            else:
                stat_entry['under_ev'] = None
        else:
            stat_entry['under_ev'] = None
        
        enhanced_stats.append(stat_entry)
    
    # Convert to DataFrame
    enhanced_df = pd.DataFrame(enhanced_stats)
    
    # Generate default output filename if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = f"player_props_stats_{timestamp}.csv"
    
    # Save to CSV
    enhanced_df.to_csv(output_file, index=False)
    print(f"Exported enhanced statistics to {output_file}")
    
    return output_file

def main(csv_file: str, min_ev: float = 3.0, export_stats: bool = True):
    """
    Main function to process the CSV file and find value bets.
    
    Args:
        csv_file: Path to the CSV file
        min_ev: Minimum EV percentage to consider a value bet
        export_stats: Whether to export enhanced statistics to a CSV file
    """
    print(f"Processing player props data from {csv_file}...")
    
    # Process the data
    props_df = process_props_data(csv_file)
    
    # Find value bets
    value_bets = find_value_bets(props_df, min_ev)
    
    if value_bets.empty:
        print("No value bets found.")
    else:
        print(f"\nFound {len(value_bets)} value bets with EV >= {min_ev}%")
        # print(value_bets.to_string(index=False))
    
    # Export enhanced statistics if requested
    if export_stats:
        # Generate output filename based on input filename
        base_name = os.path.splitext(os.path.basename(csv_file))[0]
        output_file = f"{base_name}_enhanced_stats.csv"
        export_stats_to_csv(props_df, output_file)
    
    return props_df, value_bets

def get_median_odds(bookmaker_data: str, direction: str = 'over') -> Dict:
    """
    Get the median odds across all bookmakers for a specific direction.
    
    Args:
        bookmaker_data: JSON string containing bookmaker data
        direction: 'over' or 'under'
        
    Returns:
        Dictionary with median odds information or None if no valid odds
    """
    if pd.isnull(bookmaker_data) or bookmaker_data == "":
        return None
    
    # Extract bookmaker data
    bookmakers = extract_bookmaker_odds(bookmaker_data)
    if not bookmakers:
        return None
    
    # Collect all available odds for the specified direction
    all_odds = []
    bookmaker_names = []
    
    for bookmaker, data in bookmakers.items():
        if not data.get('available', False):
            continue
            
        # Use 'odds' key instead of 'overOdds' or 'underOdds'
        odds_key = 'odds'
        if odds_key in data:
            try:
                american_odds = float(data[odds_key])
                # Convert to decimal for easier median calculation
                decimal_odds = convert_american_to_decimal(american_odds)
                all_odds.append(decimal_odds)
                bookmaker_names.append(bookmaker)
            except (ValueError, TypeError):
                continue
    
    if not all_odds:
        return None
    
    # Calculate median decimal odds
    median_decimal = np.median(all_odds)
    
    # Convert back to American odds
    median_american = convert_decimal_to_american(median_decimal)
    
    # Find the index of the closest odds to the median
    closest_idx = np.argmin(np.abs(np.array(all_odds) - median_decimal))
    closest_bookmaker = bookmaker_names[closest_idx]
    
    return {
        'american_odds': median_american,
        'decimal_odds': median_decimal,
        'bookmaker': f"median({closest_bookmaker})",  # Indicate this is a median with the closest bookmaker
        'original_odds': all_odds,
        'original_bookmakers': bookmaker_names
    }

if __name__ == "__main__":
    # Example usage
    csv_file = "nba_player_props_2025-04-16.csv"
    
    main(csv_file)
