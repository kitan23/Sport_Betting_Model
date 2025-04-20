import pandas as pd

# Load the enhanced stats file
df = pd.read_csv('nba_player_props_2025-04-16_enhanced_stats.csv')

# Count over and under props that meet the threshold
min_ev = 3.0
over_count = (df['over_ev'] >= min_ev).sum()
under_count = (df['under_ev'] >= min_ev).sum()

print(f'Over props with EV >= {min_ev}: {over_count}')
print(f'Under props with EV >= {min_ev}: {under_count}')

# Print under props that pass the threshold
if under_count > 0:
    print('\nUnder props that make the cut:')
    under_props = df[df['under_ev'] >= min_ev].sort_values('under_ev', ascending=False)
    for _, row in under_props.iterrows():
        line_diff = row['fair_line'] - row['book_line']
        print(f"{row['player']} - {row['prop_type']}: EV = {row['under_ev']:.2f}%, Line diff = {line_diff}, Bookmakers = {row['under_bookmakers']}")

# Count by line difference direction
df['line_diff'] = df['fair_line'] - df['book_line']
pos_diff_count = df[(df['line_diff'] > 0) & (df['under_ev'] >= min_ev)].shape[0]
zero_diff_count = df[(df['line_diff'] == 0) & (df['under_ev'] >= min_ev)].shape[0]
neg_diff_count = df[(df['line_diff'] < 0) & (df['under_ev'] >= min_ev)].shape[0]

print(f"\nUnder value bets by line difference direction:")
print(f"Positive line diff (fair > book): {pos_diff_count}")
print(f"Zero line diff (fair = book): {zero_diff_count}")
print(f"Negative line diff (fair < book): {neg_diff_count}")

# Compare bookmaker counts
print(f"\nMean over bookmakers per prop: {df['over_bookmakers'].mean():.2f}")
print(f"Mean under bookmakers per prop: {df['under_bookmakers'].mean():.2f}")
print(f"Ratio of over to under bookmakers: {df['over_bookmakers'].mean() / df['under_bookmakers'].mean():.2f}:1") 