import os
import glob
import pandas as pd

# Find the latest enhanced stats file
stats_files = glob.glob('*_enhanced_stats.csv')
latest_file = max(stats_files, key=os.path.getmtime) if stats_files else None

if not latest_file:
    print("No enhanced stats file found")
    exit(1)

print(f"Using stats file: {latest_file}")

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
    
    # Check for any filtering criteria
    print("\nPossible filtering criteria:")
    if 'edge' in best_props_df.columns:
        print(f"Mean edge in best_props: {best_props_df['edge'].mean():.2f}%")
        print(f"Min edge in best_props: {best_props_df['edge'].min():.2f}%")
    
    if 'ev' in best_props_df.columns:
        print(f"Mean EV in best_props: {best_props_df['ev'].mean():.2f}%")
        print(f"Min EV in best_props: {best_props_df['ev'].min():.2f}%")
    
    # Check which file generates the best_props_today.csv
    for py_file in glob.glob('*.py'):
        with open(py_file, 'r') as f:
            content = f.read()
            if 'best_props_today.csv' in content:
                print(f"\nFile that likely generates best_props_today.csv: {py_file}")
                
                # Search for filtering logic
                if 'UNDER' in content and 'OVER' in content:
                    lines = content.split('\n')
                    relevant_lines = []
                    for i, line in enumerate(lines):
                        if 'UNDER' in line or 'OVER' in line or 'best_props_today.csv' in line:
                            start = max(0, i-5)
                            end = min(len(lines), i+5)
                            relevant_lines.extend(lines[start:end])
                    
                    print("\nRelevant code snippets that might filter out UNDER props:")
                    for line in set(relevant_lines):
                        if line.strip() and ('UNDER' in line or 'OVER' in line or 'direction' in line.lower() or 'filter' in line.lower()):
                            print(f"  {line.strip()}") 