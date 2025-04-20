import pandas as pd
import os
import glob

# Find the latest enhanced stats file
stats_files = glob.glob('*_enhanced_stats.csv')
latest_file = max(stats_files, key=os.path.getmtime) if stats_files else None

if not latest_file:
    print("No enhanced stats file found")
    exit(1)

print(f"Using stats file: {latest_file}")

# Load the enhanced stats
enhanced_df = pd.read_csv(latest_file)

# Set the minimum EV threshold (same as in find_best_props.py)
min_ev = 3.0

# Analyze over props
over_props = enhanced_df[enhanced_df['over_ev'] >= min_ev].copy()
print(f"Over props with EV >= {min_ev}: {len(over_props)}")

# Analyze under props
under_props = enhanced_df[enhanced_df['under_ev'] >= min_ev].copy()
print(f"Under props with EV >= {min_ev}: {len(under_props)}")

# Check impact of bookmaker requirements
for min_bookmakers in range(1, 11):
    # For over props
    over_qualified = over_props[over_props['over_bookmakers'] >= min_bookmakers]
    over_pct = (len(over_qualified) / len(over_props)) * 100 if len(over_props) > 0 else 0
    
    # For under props
    under_qualified = under_props[under_props['under_bookmakers'] >= min_bookmakers]
    under_pct = (len(under_qualified) / len(under_props)) * 100 if len(under_props) > 0 else 0
    
    print(f"\nWith min_bookmakers = {min_bookmakers}:")
    print(f"  Over props qualifying: {len(over_qualified)}/{len(over_props)} ({over_pct:.1f}%)")
    print(f"  Under props qualifying: {len(under_qualified)}/{len(under_props)} ({under_pct:.1f}%)")

# Print details of under props
if not under_props.empty:
    print("\nDetails of under props with EV >= 3.0:")
    for _, row in under_props.iterrows():
        print(f"{row['player']} - {row['prop_type']}: " 
              f"EV = {row['under_ev']:.2f}%, "
              f"Bookmakers = {row['under_bookmakers']}, "
              f"Line diff = {row['fair_line'] - row['book_line']}")

# Recommendations
print("\nRecommendations:")
print("1. Fix the under probability calculation in calculate_stats.py (which we've already done)")
print("2. Lower the min_bookmakers requirement for under props in find_best_props.py")
print("   - Current setting: min_bookmakers=5 for both over and under")
print("   - Suggested setting: min_bookmakers=3 for under props, keep min_bookmakers=5 for over props") 