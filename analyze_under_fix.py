import pandas as pd
import numpy as np
import os
from datetime import datetime
import json
import re

# Helper functions from calculate_stats.py
def convert_american_to_decimal(american_odds: float) -> float:
    if pd.isnull(american_odds):
        return None
    
    american_odds = float(american_odds)
    if american_odds > 0:
        return round((american_odds / 100) + 1, 4)
    else:
        return round((100 / abs(american_odds)) + 1, 4)

def calculate_implied_probability(decimal_odds: float) -> float:
    if pd.isnull(decimal_odds) or decimal_odds <= 0:
        return None
    
    return round(1 / decimal_odds, 4)

def calculate_ev(bet_odds: float, true_probability: float, stake: float = 100) -> float:
    if pd.isnull(bet_odds) or pd.isnull(true_probability):
        return None
    
    # Calculate potential profit
    potential_profit = stake * (bet_odds - 1)
    
    # Calculate EV
    ev = (true_probability * potential_profit) - ((1 - true_probability) * stake)
    
    # Return as percentage
    return round((ev / stake) * 100, 2)

def calculate_no_vig_probability(over_prob: float, under_prob: float):
    if pd.isnull(over_prob) or pd.isnull(under_prob):
        return (None, None)
    
    # Calculate the overround (total probability)
    total_prob = over_prob + under_prob
    
    # Remove the vig by normalizing the probabilities
    no_vig_over = round(over_prob / total_prob, 4)
    no_vig_under = round(under_prob / total_prob, 4)
    
    return (no_vig_over, no_vig_under)

def calculate_under_ev_old_way(no_vig_under_prob, line_difference, decimal_odds):
    """Calculate under EV using the old method that always subtracts the adjustment"""
    if no_vig_under_prob is None or pd.isnull(line_difference) or pd.isnull(decimal_odds):
        return None
    
    # Calculate probability adjustment
    base_adjustment = line_difference * 0.075
    confidence_factor = 0.85
    probability_adjustment = base_adjustment * confidence_factor
    
    # Old way: always subtract adjustment
    true_under_prob = no_vig_under_prob - probability_adjustment
    true_under_prob = max(0.15, min(0.85, true_under_prob))
    
    # Calculate EV
    ev_value = calculate_ev(decimal_odds, true_under_prob)
    
    # Cap extreme values
    if ev_value is not None and abs(ev_value) > 100:
        ev_value = np.sign(ev_value) * 100
    
    return ev_value

def calculate_under_ev_new_way(no_vig_under_prob, line_difference, decimal_odds):
    """Calculate under EV using the new method that conditionally adds or subtracts the adjustment"""
    if no_vig_under_prob is None or pd.isnull(line_difference) or pd.isnull(decimal_odds):
        return None
    
    # Calculate probability adjustment
    base_adjustment = line_difference * 0.075
    confidence_factor = 0.85
    probability_adjustment = base_adjustment * confidence_factor
    
    # New way: conditional based on line difference
    if line_difference > 0:
        # Fair line > book line: lower probability (subtract adjustment)
        true_under_prob = no_vig_under_prob - probability_adjustment
    elif line_difference < 0:
        # Fair line < book line: higher probability (add adjustment)
        true_under_prob = no_vig_under_prob + probability_adjustment
    else:
        # No difference, use no-vig probability
        true_under_prob = no_vig_under_prob
    
    true_under_prob = max(0.15, min(0.85, true_under_prob))
    
    # Calculate EV
    ev_value = calculate_ev(decimal_odds, true_under_prob)
    
    # Cap extreme values
    if ev_value is not None and abs(ev_value) > 100:
        ev_value = np.sign(ev_value) * 100
    
    return ev_value

def main():
    # Load the enhanced stats file
    enhanced_df = pd.read_csv('nba_player_props_2025-04-16_enhanced_stats.csv')
    
    # Calculate line difference (since it's not in the original dataframe)
    enhanced_df['line_diff'] = enhanced_df['fair_line'] - enhanced_df['book_line']
    
    # Add columns for our recalculated EVs
    enhanced_df['simulated_old_under_ev'] = None
    enhanced_df['simulated_new_under_ev'] = None
    
    # Calculate the over/under implied probabilities and no-vig probabilities
    valid_over_under_mask = (
        enhanced_df['median_over_odds'].notna() & 
        enhanced_df['median_under_odds'].notna() & 
        enhanced_df['fair_line'].notna() & 
        enhanced_df['book_line'].notna()
    )
    
    # Only process rows with valid data
    valid_rows = enhanced_df[valid_over_under_mask].copy()
    
    for idx, row in valid_rows.iterrows():
        # Convert odds to decimal
        over_decimal = convert_american_to_decimal(row['median_over_odds'])
        under_decimal = convert_american_to_decimal(row['median_under_odds'])
        
        # Calculate implied probabilities
        over_prob = calculate_implied_probability(over_decimal) if over_decimal else None
        under_prob = calculate_implied_probability(under_decimal) if under_decimal else None
        
        # Calculate no-vig probabilities
        no_vig_over, no_vig_under = calculate_no_vig_probability(over_prob, under_prob)
        
        # Get line difference
        line_diff = row['line_diff']
        
        # Calculate under EVs using both methods
        old_under_ev = calculate_under_ev_old_way(no_vig_under, line_diff, under_decimal)
        new_under_ev = calculate_under_ev_new_way(no_vig_under, line_diff, under_decimal)
        
        # Store the results
        enhanced_df.at[idx, 'simulated_old_under_ev'] = old_under_ev
        enhanced_df.at[idx, 'simulated_new_under_ev'] = new_under_ev
    
    # Analyze the results
    min_ev = 3.0
    
    # Count value bets with each method
    old_value_count = (enhanced_df['simulated_old_under_ev'] >= min_ev).sum()
    new_value_count = (enhanced_df['simulated_new_under_ev'] >= min_ev).sum()
    orig_value_count = (enhanced_df['under_ev'] >= min_ev).sum()
    
    print(f"Original under props with EV >= {min_ev}: {orig_value_count}")
    print(f"Simulated old formula under props with EV >= {min_ev}: {old_value_count}")
    print(f"Simulated new formula under props with EV >= {min_ev}: {new_value_count}")
    
    # Calculate mean EVs
    old_mean = enhanced_df['simulated_old_under_ev'].mean()
    new_mean = enhanced_df['simulated_new_under_ev'].mean()
    orig_mean = enhanced_df['under_ev'].mean()
    
    print(f"\nOriginal under EV mean: {orig_mean:.2f}%")
    print(f"Simulated old formula under EV mean: {old_mean:.2f}%")
    print(f"Simulated new formula under EV mean: {new_mean:.2f}%")
    
    # Group by line difference sign
    enhanced_df['line_diff_sign'] = np.sign(enhanced_df['line_diff'])
    
    old_by_sign = enhanced_df.groupby('line_diff_sign')['simulated_old_under_ev'].mean()
    new_by_sign = enhanced_df.groupby('line_diff_sign')['simulated_new_under_ev'].mean()
    
    print("\nMean under EV by line difference sign (old formula):")
    print(old_by_sign)
    
    print("\nMean under EV by line difference sign (new formula):")
    print(new_by_sign)
    
    # Show the top value bets with the new formula
    new_value_props = enhanced_df[enhanced_df['simulated_new_under_ev'] >= min_ev].sort_values('simulated_new_under_ev', ascending=False)
    
    print(f"\nTop value under props with new formula (EV >= {min_ev}):")
    for _, row in new_value_props.head(10).iterrows():
        print(f"{row['player']} - {row['prop_type']}: "
              f"New EV = {row['simulated_new_under_ev']:.2f}%, "
              f"Old EV = {row['simulated_old_under_ev']:.2f}%, "
              f"Original EV = {row['under_ev']:.2f}%, "
              f"Line diff = {row['line_diff']}, "
              f"Bookmakers = {row['under_bookmakers']}")
    
    # Count by line difference direction
    pos_diff_count = enhanced_df[(enhanced_df['line_diff'] > 0) & (enhanced_df['simulated_new_under_ev'] >= min_ev)].shape[0]
    zero_diff_count = enhanced_df[(enhanced_df['line_diff'] == 0) & (enhanced_df['simulated_new_under_ev'] >= min_ev)].shape[0]
    neg_diff_count = enhanced_df[(enhanced_df['line_diff'] < 0) & (enhanced_df['simulated_new_under_ev'] >= min_ev)].shape[0]
    
    print(f"\nNew formula value bets by line difference direction:")
    print(f"Positive line diff (fair > book): {pos_diff_count}")
    print(f"Zero line diff (fair = book): {zero_diff_count}")
    print(f"Negative line diff (fair < book): {neg_diff_count}")
    
    # Compare to over props
    over_value_count = (enhanced_df['over_ev'] >= min_ev).sum()
    print(f"\nOver props with EV >= {min_ev}: {over_value_count}")
    print(f"New under props with EV >= {min_ev}: {new_value_count}")
    print(f"Ratio of over to under value props: {over_value_count / max(new_value_count, 1):.1f}:1")
    
    # Availability of under bookmakers compared to over bookmakers
    print(f"\nMean over bookmakers per prop: {enhanced_df['over_bookmakers'].mean():.2f}")
    print(f"Mean under bookmakers per prop: {enhanced_df['under_bookmakers'].mean():.2f}")
    print(f"Ratio of over to under bookmakers: {enhanced_df['over_bookmakers'].mean() / enhanced_df['under_bookmakers'].mean():.2f}:1")

if __name__ == "__main__":
    main() 