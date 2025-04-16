"""
Sports Betting Model - Find Best Props Module

This module contains functions to find the best player props to bet on from the enhanced stats CSV.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import glob

def filter_duplicate_props(combined_props):
    """
    Filter out duplicate props where both OVER and UNDER exist for the same player and prop type.
    Only keep the prop with the higher EV value.
    
    Args:
        combined_props: DataFrame with combined OVER and UNDER props
        
    Returns:
        DataFrame with filtered props where duplicates are removed
    """
    # If the DataFrame is empty, return it as is
    if combined_props.empty:
        return combined_props
    
    # Create a copy to avoid modifying the original DataFrame
    filtered_props = combined_props.copy()
    
    # Convert string percentages back to floats for comparison
    if 'ev' in filtered_props.columns and isinstance(filtered_props['ev'].iloc[0], str):
        filtered_props['ev_float'] = filtered_props['ev'].str.rstrip('%').astype(float)
    else:
        if 'ev' in filtered_props.columns:
            filtered_props['ev_float'] = filtered_props['ev']
        else:
            # If 'ev' column doesn't exist, create a default ev_float column
            filtered_props['ev_float'] = 0
    
    # Create a unique identifier for each player-prop combination
    filtered_props['prop_id'] = filtered_props['player'] + '_' + filtered_props['prop_type'] + '_' + filtered_props['fair_line'].astype(str) + '_' + filtered_props['book_line'].astype(str)
    
    # Find duplicates (same player, prop_type, fair_line, and book_line but different bet_type)
    duplicates = filtered_props['prop_id'].duplicated(keep=False)
    duplicate_props = filtered_props[duplicates].copy()
    
    # Keep non-duplicate props
    unique_props = filtered_props[~duplicates].copy()
    
    # Process duplicates to keep only the higher EV prop
    if not duplicate_props.empty:
        # Sort duplicates by prop_id and ev_float (descending)
        duplicate_props = duplicate_props.sort_values(['prop_id', 'ev_float'], ascending=[True, False])
        
        # Keep only the first occurrence of each prop_id (highest EV)
        best_duplicates = duplicate_props.drop_duplicates(subset='prop_id', keep='first')
        
        # Combine unique props with best duplicates
        result = pd.concat([unique_props, best_duplicates])
        
        # Drop the temporary columns
        columns_to_drop = ['prop_id', 'ev_float']
        result = result.drop(columns=[col for col in columns_to_drop if col in result.columns])
        
        # Sort by score again if the column exists
        if 'score' in result.columns:
            result = result.sort_values('score', ascending=False)
        
        return result
    else:
        # If no duplicates, return the original DataFrame without the temporary columns
        columns_to_drop = ['prop_id', 'ev_float']
        return unique_props.drop(columns=[col for col in columns_to_drop if col in unique_props.columns])

def calculate_adjusted_score(ev: float, edge: float, american_odds: float) -> float:
    """
    Calculate an adjusted score that better accounts for plus odds value.
    
    Args:
        ev: Expected value percentage
        edge: Edge percentage (true_prob - implied_prob)
        american_odds: American odds value
        
    Returns:
        Adjusted score value
    """
    # Base score using weighted sum of EV and edge
    base_score = (ev * 0.7) + (edge * 100 * 0.3)
    
    # Add bonus for plus odds
    if american_odds > 0:
        return base_score * 1.1  # 10% bonus for plus odds
    return base_score

def find_best_props(csv_file, max_ev_threshold=80, min_ev_threshold=0, min_bookmakers=3, exclude_keywords=None, num_props=100):
    """
    Find the best player props to bet on from the enhanced stats CSV.
    
    Args:
        csv_file: Path to the enhanced stats CSV file
        max_ev_threshold: Maximum EV to consider (to filter out unrealistic values)
        min_ev_threshold: Minimum EV to consider (default: 0%)
        min_bookmakers: Minimum number of bookmakers offering the prop
        exclude_keywords: List of keywords to exclude from prop_type (default: ["steals", "blocks"])
        num_props: Number of top props to return (default: 100)
        
    Returns:
        DataFrame with the top recommended props
    """
    # Set default exclude keywords if None
    if exclude_keywords is None:
        exclude_keywords = ["steals", "blocks"]
    
    print(f"Analyzing props from {csv_file}...")
    print(f"Excluding props containing: {', '.join(exclude_keywords)}")
    print(f"Minimum bookmakers: {min_bookmakers}")
    print(f"EV range: {min_ev_threshold}% to {max_ev_threshold}%")
    print(f"Number of props to return: {num_props}")
    
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} props from the CSV file")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return pd.DataFrame()
    
    # Filter out props with too few bookmakers
    df_filtered = df[df['total_bookmakers'] >= min_bookmakers].copy()
    print(f"Found {len(df_filtered)} props with at least {min_bookmakers} bookmakers")
    
    # Filter out props with excluded keywords
    if exclude_keywords:
        for keyword in exclude_keywords:
            df_filtered = df_filtered[~df_filtered['prop_type'].str.contains(keyword, case=False)]
        print(f"Found {len(df_filtered)} props after excluding keywords")
    
    # Filter out props with unusually large line differences
    max_line_diff = 2.0  # Maximum allowed difference between fair_line and book_line
    df_filtered = df_filtered[abs(df_filtered['fair_line'] - df_filtered['book_line']) <= max_line_diff]
    print(f"Found {len(df_filtered)} props after filtering out large line differences")
    
    # Create separate DataFrames for over and under props
    over_props = df_filtered.copy()
    under_props = df_filtered.copy()
    
    # Filter out unrealistic EV values and ensure minimum EV
    over_props = over_props[(over_props['over_ev'] <= max_ev_threshold) & 
                           (over_props['over_ev'] >= min_ev_threshold)]
    under_props = under_props[(under_props['under_ev'] <= max_ev_threshold) & 
                             (under_props['under_ev'] >= min_ev_threshold)]
    
    print(f"Found {len(over_props)} over props and {len(under_props)} under props with EV between {min_ev_threshold}% and {max_ev_threshold}%")
    
    # Calculate edges and scores with the new scoring system
    if not over_props.empty:
        over_props['edge'] = over_props['no_vig_over_prob'] - over_props['over_implied_prob']
        over_props['score'] = over_props.apply(
            lambda x: calculate_adjusted_score(x['over_ev'], x['edge'], x['median_over_odds']), 
            axis=1
        )
        over_props['bet_type'] = 'OVER'
        over_props['ev'] = over_props['over_ev']
        over_props['implied_prob'] = over_props['over_implied_prob']
        over_props['true_prob'] = over_props['no_vig_over_prob']
        over_props['american_odds'] = over_props['median_over_odds']
        over_props['bookmaker'] = over_props['median_over_bookmaker']
    
    if not under_props.empty:
        under_props['edge'] = under_props['no_vig_under_prob'] - under_props['under_implied_prob']
        under_props['score'] = under_props.apply(
            lambda x: calculate_adjusted_score(x['under_ev'], x['edge'], x['median_under_odds']), 
            axis=1
        )
        under_props['bet_type'] = 'UNDER'
        under_props['ev'] = under_props['under_ev']
        under_props['implied_prob'] = under_props['under_implied_prob']
        under_props['true_prob'] = under_props['no_vig_under_prob']
        under_props['american_odds'] = under_props['median_under_odds']
        under_props['bookmaker'] = under_props['median_under_bookmaker']
    
    # Combine the over and under props
    columns_to_keep = ['player', 'prop_type', 'fair_line', 'book_line', 'bet_type', 
                       'ev', 'edge', 'score', 'implied_prob', 'true_prob', 
                       'american_odds', 'bookmaker', 'total_bookmakers', 'game']
    
    combined_props = pd.DataFrame()
    if not over_props.empty:
        combined_props = pd.concat([combined_props, over_props[columns_to_keep]])
    if not under_props.empty:
        combined_props = pd.concat([combined_props, under_props[columns_to_keep]])
    
    # Sort by the combined score if it exists
    if not combined_props.empty and 'score' in combined_props.columns:
        combined_props = combined_props.sort_values('score', ascending=False)
    
    # Correct bet direction based on fair line vs book line comparison
    if not combined_props.empty:
        # Create a copy to avoid SettingWithCopyWarning
        combined_props = combined_props.copy()
        
        # Ensure the score column exists
        if 'score' not in combined_props.columns:
            # Calculate the score if it doesn't exist
            combined_props['edge'] = combined_props.apply(
                lambda x: (x['true_prob'] - x['implied_prob']) if 'true_prob' in combined_props.columns and 'implied_prob' in combined_props.columns else 0,
                axis=1
            )
            
            combined_props['score'] = combined_props.apply(
                lambda x: calculate_adjusted_score(
                    float(x['ev'].replace('%', '')) if isinstance(x['ev'], str) else x['ev'], 
                    x['edge'], 
                    float(x['american_odds'].replace('+', '')) if isinstance(x['american_odds'], str) and '+' in x['american_odds'] else float(x['american_odds'])
                ),
                axis=1
            )
        
        # Check for inconsistencies in bet direction
        for idx, row in combined_props.iterrows():
            fair_line = row['fair_line']
            book_line = row['book_line']
            bet_type = row['bet_type']
            american_odds = row['american_odds']
            
            # Enhanced logic for determining bet direction:
            # 1. If fair line > book line, bet should be OVER
            # 2. If fair line < book line, bet should be UNDER
            # 3. If fair line == book line, keep the original bet type (based on EV)
            if fair_line > book_line and bet_type == 'UNDER':
                print(f"Warning: Correcting inconsistent bet direction for {row['player']} {row['prop_type']}")
                print(f"  Fair line ({fair_line}) > Book line ({book_line}), changing bet from UNDER to OVER")
                combined_props.at[idx, 'bet_type'] = 'OVER'
            elif fair_line < book_line and bet_type == 'OVER':
                print(f"Warning: Correcting inconsistent bet direction for {row['player']} {row['prop_type']}")
                print(f"  Fair line ({fair_line}) < Book line ({book_line}), changing bet from OVER to UNDER")
                combined_props.at[idx, 'bet_type'] = 'UNDER'
    
    # Filter out duplicate props (keep only the higher EV one)
    if not combined_props.empty:
        combined_props = filter_duplicate_props(combined_props)
        print(f"Found {len(combined_props)} props after filtering duplicates")
    else:
        print("No props found matching the criteria")
    
    # Get the top n props
    top_props = combined_props.head(num_props) if not combined_props.empty else combined_props
    
    # Format the output for better readability
    if not top_props.empty:
        # Create a copy to avoid SettingWithCopyWarning
        top_props = top_props.copy()
        top_props['american_odds'] = top_props['american_odds'].apply(lambda x: f"+{int(x)}" if x > 0 else f"{int(x)}")
        top_props['ev'] = top_props['ev'].apply(lambda x: f"{x:.2f}%")
        top_props['implied_prob'] = top_props['implied_prob'].apply(lambda x: f"{x*100:.1f}%")
        top_props['true_prob'] = top_props['true_prob'].apply(lambda x: f"{x*100:.1f}%")
        top_props['edge'] = top_props['edge'].apply(lambda x: f"{x*100:.1f}%")
    
    return top_props

def export_best_props_to_csv(top_props, output_file=None):
    """
    Export the top recommended props to a CSV file.
    
    Args:
        top_props: DataFrame with the top recommended props
        output_file: Path to the output CSV file (if None, a default name will be generated)
        
    Returns:
        Path to the created CSV file
    """
    if top_props.empty:
        print("No props to export.")
        return None
    
    # Generate default output filename if not provided
    if output_file is None:
        output_file = f"best_props_today.csv"
    
    # Create a copy of the DataFrame to avoid modifying the original
    export_df = top_props.copy()
    
    # Export to CSV
    export_df.to_csv(output_file, index=False)
    print(f"Exported {len(export_df)} best props to {output_file}")
    
    return output_file

def display_recommendations(top_props):
    """
    Display the top recommended props in a readable format.
    
    Args:
        top_props: DataFrame with the top recommended props
    """
    if top_props.empty:
        print("No recommended props found.")
        return
    
    print(f"\n===== TOP {len(top_props)} RECOMMENDED PLAYER PROPS =====\n")
    
    for i, (_, prop) in enumerate(top_props.iterrows(), 1):
        print(f"{i}. {prop['player']} - {prop['prop_type']} {prop['book_line']} {prop['bet_type']}")
        print(f"   Game: {prop['game']}")
        print(f"   Odds: {prop['american_odds']} ({prop['bookmaker']})")
        print(f"   Fair Line: {prop['fair_line']} (vs Book Line: {prop['book_line']})")
        print(f"   EV: {prop['ev']} | Edge: {prop['edge']}")
        print(f"   Implied Probability: {prop['implied_prob']} | True Probability: {prop['true_prob']}")
        print(f"   Bookmakers: {prop['total_bookmakers']}")
        print()

if __name__ == "__main__":
    try:
        # Find the most recent enhanced stats CSV file
        csv_files = [f for f in os.listdir('.') if f.endswith('_enhanced_stats.csv')]
        if not csv_files:
            print("No enhanced stats CSV files found.")
        else:
            # Sort by modification time (most recent first)
            csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            most_recent_csv = csv_files[0]
            print(f"Using most recent CSV file: {most_recent_csv}")
            
            # Find the best props with reasonable EV threshold
            print("\n=== Finding Best Props ===")
            top_props = find_best_props(
                most_recent_csv,
                min_ev_threshold=3,      # Only include props with positive EV
                min_bookmakers=3,        # Maintain reduced bookmakers requirement
                exclude_keywords=["steals", "blocks"],
                num_props=100
            )
            
            # Display and export the results
            if not top_props.empty:
                display_recommendations(top_props)
                export_best_props_to_csv(top_props)
                print(f"Successfully exported {len(top_props)} props to best_props_today.csv")
            else:
                print("No props found to display or export.")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

# Find the latest enhanced stats file
stats_files = glob.glob('*_enhanced_stats.csv')
latest_file = max(stats_files, key=os.path.getmtime) if stats_files else None

if not latest_file:
    print("No enhanced stats file found")
    exit(1)

# Load the enhanced stats and best props files
enhanced_df = pd.read_csv(latest_file)
best_props_file = 'best_props_today.csv'

if os.path.exists(best_props_file):
    best_props_df = pd.read_csv(best_props_file)
    print(f"Loaded {len(best_props_df)} best props from {best_props_file}")
else:
    print(f"Best props file {best_props_file} not found")
    best_props_df = pd.DataFrame()

# Check what props meet the EV threshold
min_ev = 3.0
over_props = enhanced_df[enhanced_df['over_ev'] >= min_ev].copy()
under_props = enhanced_df[enhanced_df['under_ev'] >= min_ev].copy()

print(f"Props with over EV >= {min_ev}: {len(over_props)}")
print(f"Props with under EV >= {min_ev}: {len(under_props)}")

# Check if the under props are in the best_props file
if not best_props_df.empty and not under_props.empty:
    # Try to match on player, prop_type, direction
    for _, under_row in under_props.iterrows():
        player_name = under_row['player']
        prop_type = under_row['prop_type']
        
        matching_rows = best_props_df[
            (best_props_df['player'] == player_name) & 
            (best_props_df['prop_type'] == prop_type) &
            (best_props_df['bet_type'] == 'UNDER')
        ]
        
        if not matching_rows.empty:
            print(f"Found matching under prop in best_props_today.csv: {player_name} - {prop_type}")
        else:
            print(f"Under prop NOT found in best_props_today.csv: {player_name} - {prop_type}")
else:
    print("Could not check for under props in best_props_today.csv")

# Check for any code that might filter out under props
print("\nPossible filters applied to props:")
if 'bookmaker_count' in enhanced_df.columns:
    print(f"Mean bookmaker count for all props: {enhanced_df['bookmaker_count'].mean():.2f}")
    print(f"Mean bookmaker count for over props with EV >= {min_ev}: {over_props['bookmaker_count'].mean() if not over_props.empty else 'N/A'}")
    print(f"Mean bookmaker count for under props with EV >= {min_ev}: {under_props['bookmaker_count'].mean() if not under_props.empty else 'N/A'}")

if 'over_bookmakers' in enhanced_df.columns and 'under_bookmakers' in enhanced_df.columns:
    print(f"Mean over bookmakers: {enhanced_df['over_bookmakers'].mean():.2f}")
    print(f"Mean under bookmakers: {enhanced_df['under_bookmakers'].mean():.2f}")
    
    if not over_props.empty:
        print(f"Mean over bookmakers for props with over EV >= {min_ev}: {over_props['over_bookmakers'].mean():.2f}")
    
    if not under_props.empty:
        print(f"Mean under bookmakers for props with under EV >= {min_ev}: {under_props['under_bookmakers'].mean():.2f}")

# Look at the distribution of bet types in best_props
if not best_props_df.empty and 'bet_type' in best_props_df.columns:
    bet_type_counts = best_props_df['bet_type'].value_counts()
    print("\nBet type distribution in best_props_today.csv:")
    for bet_type, count in bet_type_counts.items():
        print(f"{bet_type}: {count} ({count/len(best_props_df)*100:.1f}%)")