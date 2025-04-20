import pandas as pd
import numpy as np

# Load the enhanced stats file to see distributions of over vs under EVs
enhanced_df = pd.read_csv('nba_player_props_2025-04-16_enhanced_stats.csv')

# Count how many over and under EVs are not null
over_count = enhanced_df['over_ev'].notna().sum()
under_count = enhanced_df['under_ev'].notna().sum()
print(f'Rows with over_ev not null: {over_count}')
print(f'Rows with under_ev not null: {under_count}')

# Get stats on over and under EVs
over_mean = enhanced_df['over_ev'].mean()
under_mean = enhanced_df['under_ev'].mean()
print(f'Mean over_ev: {over_mean}')
print(f'Mean under_ev: {under_mean}')

# Count how many over and under EVs meet the min_ev threshold of 3.0
min_ev = 3.0
over_value_bets = (enhanced_df['over_ev'] >= min_ev).sum()
under_value_bets = (enhanced_df['under_ev'] >= min_ev).sum()
print(f'Over props with EV >= {min_ev}: {over_value_bets}')
print(f'Under props with EV >= {min_ev}: {under_value_bets}')

# Count bookmakers for over vs under
over_bookmakers_mean = enhanced_df['over_bookmakers'].mean()
under_bookmakers_mean = enhanced_df['under_bookmakers'].mean()
print(f'Mean over bookmakers: {over_bookmakers_mean}')
print(f'Mean under bookmakers: {under_bookmakers_mean}')

# Print a sample of rows with high under EVs for inspection
high_under_ev_rows = enhanced_df[enhanced_df['under_ev'] >= 0].sort_values('under_ev', ascending=False).head(5)
print('\nTop 5 under props by EV:')
for _, row in high_under_ev_rows.iterrows():
    print(f"{row['player']} - {row['prop_type']}: EV = {row['under_ev']}%, Bookmakers = {row['under_bookmakers']}")

# Print a sample of rows with high over EVs for comparison
high_over_ev_rows = enhanced_df[enhanced_df['over_ev'] >= 0].sort_values('over_ev', ascending=False).head(5)
print('\nTop 5 over props by EV:')
for _, row in high_over_ev_rows.iterrows():
    print(f"{row['player']} - {row['prop_type']}: EV = {row['over_ev']}%, Bookmakers = {row['over_bookmakers']}")

# Analyze line differences and their impact on probability
print("\nAnalyzing line differences and probability adjustments:")
enhanced_df['line_diff'] = enhanced_df['fair_line'] - enhanced_df['book_line']

# Calculate what the probability adjustments would be
enhanced_df['base_adjustment'] = enhanced_df['line_diff'] * 0.075
enhanced_df['prob_adjustment'] = enhanced_df['base_adjustment'] * 0.85

# For over props, add the adjustment; for under props, subtract the adjustment
print("\nAverage line difference:", enhanced_df['line_diff'].mean())
print("Average base adjustment:", enhanced_df['base_adjustment'].mean())
print("Average probability adjustment:", enhanced_df['prob_adjustment'].mean())

# Show the distribution of line differences
print("\nLine difference distribution:")
print(enhanced_df['line_diff'].describe())

# Investigate how line differences affect under EVs vs over EVs
# For under props, positive line_diff should lead to lower true_prob
# For over props, positive line_diff should lead to higher true_prob
# Group by sign of line_diff and average EV
print("\nEV by line difference direction:")
enhanced_df['line_diff_sign'] = np.sign(enhanced_df['line_diff'])
ev_by_sign = enhanced_df.groupby('line_diff_sign')[['over_ev', 'under_ev']].mean()
print(ev_by_sign)

# Calculate how often line differences are in each direction
print("\nLine difference direction frequency:")
line_diff_counts = enhanced_df['line_diff_sign'].value_counts(normalize=True).sort_index() * 100
print(line_diff_counts.apply(lambda x: f"{x:.1f}%"))

# Check if the calculation creates values that are negative when they should be positive
# For under props: if fair_line > book_line, true probability should be LOWER
# For over props: if fair_line > book_line, true probability should be HIGHER
enhanced_df['expected_under_adjustment_sign'] = -np.sign(enhanced_df['line_diff'])
enhanced_df['expected_over_adjustment_sign'] = np.sign(enhanced_df['line_diff'])

# Calculate actual adjustment effect on EV by comparing to no_vig_prob
# Over EV tends to be positive when prob_adjustment is positive and aligned with expected
# Under EV tends to be positive when prob_adjustment is negative and aligned with expected
enhanced_df['over_adj_alignment'] = np.sign(enhanced_df['prob_adjustment']) == enhanced_df['expected_over_adjustment_sign']
enhanced_df['under_adj_alignment'] = np.sign(-enhanced_df['prob_adjustment']) == enhanced_df['expected_under_adjustment_sign']

print("\nOver prop EV when adjustment is aligned vs not aligned:")
print(enhanced_df.groupby('over_adj_alignment')['over_ev'].mean())

print("\nUnder prop EV when adjustment is aligned vs not aligned:")
print(enhanced_df.groupby('under_adj_alignment')['under_ev'].mean())

# Print the number of props where the adjustment for unders is in the wrong direction
wrong_adj_unders = enhanced_df[~enhanced_df['under_adj_alignment']].shape[0]
total_unders = enhanced_df.shape[0]
print(f"\nUnder props with incorrectly aligned probability adjustment: {wrong_adj_unders}/{total_unders} ({wrong_adj_unders/total_unders*100:.1f}%)")

# Check if there's a mistake in how true_under_prob is calculated
# The key line in calculate_stats.py is: true_under_prob = no_vig_under_prob - probability_adjustment
# For under props:
# If fair_line > book_line (positive diff), we should SUBTRACT adjustment (making true prob LOWER)
# If fair_line < book_line (negative diff), we should ADD adjustment (making true prob HIGHER)
print("\nProblem check - under EV calculation when line_diff is positive vs negative:")
under_ev_by_line_diff = enhanced_df.groupby(enhanced_df['line_diff'] > 0)['under_ev'].mean()
print(under_ev_by_line_diff)

# Let's look at specific examples with high line differences in both directions
print("\nExamples of positive line differences (fair_line > book_line):")
pos_diff_examples = enhanced_df[enhanced_df['line_diff'] > 1].sort_values('line_diff', ascending=False).head(3)
for _, row in pos_diff_examples.iterrows():
    line_diff = row['line_diff']
    prob_adj = row['prob_adjustment']
    under_ev = row['under_ev']
    over_ev = row['over_ev']
    print(f"{row['player']} - {row['prop_type']}: line_diff={line_diff:.1f}, prob_adj={prob_adj:.3f}, over_EV={over_ev:.1f}%, under_EV={under_ev:.1f}%")

print("\nExamples of negative line differences (fair_line < book_line):")
neg_diff_examples = enhanced_df[enhanced_df['line_diff'] < -1].sort_values('line_diff').head(3)
for _, row in neg_diff_examples.iterrows():
    line_diff = row['line_diff']
    prob_adj = row['prob_adjustment']
    under_ev = row['under_ev']
    over_ev = row['over_ev']
    print(f"{row['player']} - {row['prop_type']}: line_diff={line_diff:.1f}, prob_adj={prob_adj:.3f}, over_EV={over_ev:.1f}%, under_EV={under_ev:.1f}%")

# Add a section to simulate what would happen if we fixed the formula
print("\n\n*** SIMULATION OF FIXED UNDER PROBABILITY CALCULATION ***")

# The correct formula would use the opposite sign of the probability adjustment
# Calculate what the correct true probability for unders would be
enhanced_df['correct_true_under_prob'] = np.nan

# Only process rows with non-null values for the necessary fields
valid_rows = enhanced_df[enhanced_df['no_vig_under_prob'].notna() & enhanced_df['prob_adjustment'].notna()]

for idx, row in valid_rows.iterrows():
    line_diff = row['line_diff']
    no_vig_under_prob = row['no_vig_under_prob']
    prob_adj = row['prob_adjustment']
    
    # The correct formula: ADD adjustment when line_diff < 0, SUBTRACT when line_diff > 0
    if line_diff > 0:
        # If fair_line > book_line, SUBTRACT adjustment (true probability of going under is LOWER)
        correct_under_prob = no_vig_under_prob - prob_adj
    elif line_diff < 0:
        # If fair_line < book_line, ADD adjustment (true probability of going under is HIGHER)
        correct_under_prob = no_vig_under_prob + prob_adj
    else:
        # No line difference, no adjustment needed
        correct_under_prob = no_vig_under_prob
    
    # Apply the same clamping as in the original code
    correct_under_prob = max(0.15, min(0.85, correct_under_prob))
    enhanced_df.at[idx, 'correct_true_under_prob'] = correct_under_prob

# Calculate what the EV would be with the corrected probability
enhanced_df['simulated_under_ev'] = np.nan

# Only process rows where we have median_under odds and the corrected probability
valid_rows = enhanced_df[enhanced_df['correct_true_under_prob'].notna() & enhanced_df['median_under_odds'].notna()]

# Define a function to calculate EV similar to the one in calculate_stats.py
def sim_calculate_ev(decimal_odds, true_probability):
    if pd.isnull(decimal_odds) or pd.isnull(true_probability):
        return None
    
    stake = 100  # Same default as in calculate_stats.py
    potential_profit = stake * (decimal_odds - 1)
    ev = (true_probability * potential_profit) - ((1 - true_probability) * stake)
    return round((ev / stake) * 100, 2)

# Apply the EV calculation to each valid row
for idx, row in valid_rows.iterrows():
    # First convert american odds to decimal
    american_odds = row['median_under_odds']
    if not pd.isnull(american_odds):
        decimal_odds = None
        if american_odds > 0:
            decimal_odds = round((american_odds / 100) + 1, 4)
        else:
            decimal_odds = round((100 / abs(american_odds)) + 1, 4)
        
        if decimal_odds:
            # Calculate the EV with the corrected probability
            ev_value = sim_calculate_ev(decimal_odds, row['correct_true_under_prob'])
            
            # Cap extreme values as in the original code
            if ev_value is not None and abs(ev_value) > 100:
                ev_value = np.sign(ev_value) * 100
                
            enhanced_df.at[idx, 'simulated_under_ev'] = ev_value

# Count how many under props would have EV above the threshold with the fixed calculation
simulated_under_value_bets = (enhanced_df['simulated_under_ev'] >= min_ev).sum()
print(f'Simulated under props with EV >= {min_ev}: {simulated_under_value_bets} (vs {under_value_bets} with current formula)')

# Show the top simulated under props
high_sim_under_ev_rows = enhanced_df[enhanced_df['simulated_under_ev'] >= min_ev].sort_values('simulated_under_ev', ascending=False).head(10)
print('\nTop simulated under props by EV:')
for _, row in high_sim_under_ev_rows.iterrows():
    print(f"{row['player']} - {row['prop_type']}: " 
          f"Simulated EV = {row['simulated_under_ev']:.2f}%, "
          f"Current EV = {row['under_ev']:.2f}%, "
          f"Line diff = {row['line_diff']}, "
          f"Bookmakers = {row['under_bookmakers']}")

# Compare distributions of current vs simulated under EVs
print("\nCurrent under EV stats:")
print(enhanced_df['under_ev'].describe())

print("\nSimulated under EV stats:")
print(enhanced_df['simulated_under_ev'].describe())

# Count by line difference direction
positive_diff_sim_value = enhanced_df[(enhanced_df['line_diff'] > 0) & (enhanced_df['simulated_under_ev'] >= min_ev)].shape[0]
zero_diff_sim_value = enhanced_df[(enhanced_df['line_diff'] == 0) & (enhanced_df['simulated_under_ev'] >= min_ev)].shape[0]
negative_diff_sim_value = enhanced_df[(enhanced_df['line_diff'] < 0) & (enhanced_df['simulated_under_ev'] >= min_ev)].shape[0]

print(f"\nSimulated value bets by line difference direction:")
print(f"Positive line diff (fair > book): {positive_diff_sim_value}")
print(f"Zero line diff (fair = book): {zero_diff_sim_value}")
print(f"Negative line diff (fair < book): {negative_diff_sim_value}") 