"""
Sports Betting Model - Bookmaker Comparison Module

This module allows users to compare odds from a specific bookmaker against other bookmakers
to identify potential edges and better values.

Works with the raw props data from data_processing.py, not the enhanced stats file.
"""

import pandas as pd
import numpy as np
import json
import argparse
from typing import Dict, Tuple, List, Optional
import os
import glob
import re

# Recycled functions from calculate_stats.py
def convert_american_to_decimal(american_odds: float) -> float:
    """
    Convert American odds to decimal odds.
    
    Args:
        american_odds: American odds format
        
    Returns:
        Decimal odds
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
        decimal_odds: Decimal odds format
        
    Returns:
        American odds (rounded to nearest integer)
    """
    if pd.isnull(decimal_odds) or decimal_odds <= 1:
        return None
    
    if decimal_odds < 2:
        american_odds = -100 / (decimal_odds - 1)
    else:
        american_odds = (decimal_odds - 1) * 100
    
    return int(round(american_odds))

def calculate_implied_probability(decimal_odds: float) -> float:
    """
    Calculate the implied probability from decimal odds.
    
    Args:
        decimal_odds: Decimal odds format
        
    Returns:
        Implied probability (0-1)
    """
    if pd.isnull(decimal_odds) or decimal_odds <= 0:
        return None
    
    return round(1 / decimal_odds, 4)

def extract_bookmaker_from_raw_props(props_df: pd.DataFrame) -> List[str]:
    """
    Extract all unique bookmakers from the raw player props data.
    
    Args:
        props_df: DataFrame containing player props from data_processing.py
        
    Returns:
        List of unique bookmaker names
    """
    # Check if byBookmaker column exists
    if 'byBookmaker' not in props_df.columns:
        print("Error: byBookmaker column not found in the data")
        return []
    
    # Try to parse a sample to see what format the data is in
    sample = props_df['byBookmaker'].dropna().iloc[0] if not props_df['byBookmaker'].dropna().empty else None
    print(f"Sample from byBookmaker column: {str(sample)[:100]}...")
    
    # Parse all bookmaker data
    bookmakers = set()
    for data in props_df['byBookmaker'].dropna():
        try:
            if isinstance(data, str):
                # Try different JSON parsing approaches
                try:
                    # Standard JSON parsing
                    bookie_data = json.loads(data)
                    bookmakers.update(bookie_data.keys())
                except json.JSONDecodeError:
                    # Try with eval (safer than raw eval)
                    import ast
                    bookie_data = ast.literal_eval(data)
                    bookmakers.update(bookie_data.keys())
            elif isinstance(data, dict):
                # Already a dictionary
                bookmakers.update(data.keys())
        except Exception as e:
            print(f"Error parsing bookmaker data: {str(e)[:100]}")
            continue
    
    if not bookmakers:
        print("\nFailed to extract bookmakers. Trying alternative approach...")
        # Try a more aggressive approach with regex
        for data in props_df['byBookmaker'].dropna():
            if isinstance(data, str):
                # Look for patterns like "bookmaker": or 'bookmaker':
                bookmaker_matches = re.findall(r'["\']([^"\']+)["\']:\s*{', data)
                bookmakers.update(bookmaker_matches)
    
    if bookmakers:
        print(f"Found {len(bookmakers)} bookmakers: {', '.join(sorted(list(bookmakers))[:5])}...")
    else:
        print("Could not extract any bookmakers. Check if the JSON format is valid.")
    

    print("Example bookmaker:", sorted(list(bookmakers)))
    return sorted(list(bookmakers))

def calculate_edge(target_decimal_odds: float, median_decimal_odds: float) -> float:
    """
    Calculate the edge between target bookmaker odds and median odds.
    
    Args:
        target_decimal_odds: Decimal odds from target bookmaker
        median_decimal_odds: Median decimal odds across bookmakers
        
    Returns:
        Edge percentage (positive means value on target bookmaker)
    """
    if target_decimal_odds is None or median_decimal_odds is None:
        return None
    
    target_prob = calculate_implied_probability(target_decimal_odds)
    median_prob = calculate_implied_probability(median_decimal_odds)
    
    if target_prob is None or median_prob is None:
        return None
    
    # Edge is the difference in implied probabilities
    # Positive edge means the target bookmaker has better value
    return round((median_prob - target_prob) * 100, 2)

def parse_bookmaker_json(data):
    """
    Parse the byBookmaker JSON data using multiple methods.
    
    Args:
        data: JSON string or dict from byBookmaker column
        
    Returns:
        Parsed dictionary or empty dict if parsing fails
    """
    if pd.isnull(data):
        return {}
        
    # If already a dict, return it
    if isinstance(data, dict):
        return data
    
    # If not a string, can't parse
    if not isinstance(data, str):
        return {}
    
    # Try different parsing methods
    try:
        # Standard JSON parse
        return json.loads(data)
    except json.JSONDecodeError:
        try:
            # Try with ast.literal_eval (safer than eval)
            import ast
            return ast.literal_eval(data)
        except:
            try:
                # Try replacing single quotes with double quotes
                fixed_data = data.replace("'", '"')
                return json.loads(fixed_data)
            except:
                # Last resort: try regex to extract key-value pairs
                result = {}
                # Look for patterns like "bookmaker": {data} or 'bookmaker': {data}
                matches = re.findall(r'["\']([^"\']+)["\']:\s*({[^{}]*})', data)
                for bookie, bookie_data in matches:
                    try:
                        bookie_dict = json.loads(bookie_data)
                        result[bookie] = bookie_dict
                    except:
                        # Just add basic data
                        result[bookie] = {"available": True}
                return result

def find_value_plays_raw(props_df: pd.DataFrame, target_bookmaker: str, min_edge: float = 2.0) -> pd.DataFrame:
    """
    Find props where the target bookmaker offers better value compared to median odds
    from the raw props data from data_processing.py.
    
    Args:
        props_df: DataFrame containing player props data
        target_bookmaker: Name of the target bookmaker
        min_edge: Minimum edge percentage to consider (default: 2.0%)
        
    Returns:
        DataFrame with value plays
    """
    results = []
    
    # Ensure we have the byBookmaker column
    if 'byBookmaker' not in props_df.columns:
        print("Error: byBookmaker column not found in data. This function requires raw props data from data_processing.py")
        return pd.DataFrame()
    
    required_cols = ['player_name', 'prop_type', 'direction', 'byBookmaker']
    missing_cols = [col for col in required_cols if col not in props_df.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}")
        return pd.DataFrame()
    
    # Track props for debugging
    processed_count = 0
    valid_prop_count = 0
    outlier_count = 0
    
    # Configuration for filtering outliers
    MAX_LINE_DIFFERENCE = 2.0       # Maximum allowable line difference
    MAX_ODDS_DIFFERENCE = 300       # Maximum allowable odds difference in American odds
    MIN_BOOKMAKERS_REQUIRED = 2     # Minimum number of other bookmakers needed for comparison
    
    # Process each prop
    for idx, prop in props_df.iterrows():
        if idx % 1000 == 0:
            print(f"Processing prop {idx}/{len(props_df)}...")
            
        player = prop['player_name'] if 'player_name' in prop else prop.get('player', 'Unknown')
        prop_type = prop['prop_type']
        direction = prop['direction']
        
        # Parse the byBookmaker JSON data
        bookmaker_data = parse_bookmaker_json(prop['byBookmaker'])
        
        if not bookmaker_data:
            continue
            
        processed_count += 1
        
        # Skip if target bookmaker not available
        if target_bookmaker not in bookmaker_data:
            continue
        
        # Get target bookmaker odds and line
        target_book_info = bookmaker_data[target_bookmaker]
        
        # Check if the target bookmaker has this prop available
        if not isinstance(target_book_info, dict) or not target_book_info.get('available', False):
            continue
        
        # Get the odds and line for target bookmaker
        target_odds = target_book_info.get('odds', None)
        
        # FIXED: Get line with fallbacks for different field names in the JSON
        # Try 'overUnder' first, then check for 'line' and 'total'
        target_line = None
        for line_field in ['overUnder', 'line', 'total', 'value']:
            if line_field in target_book_info and target_book_info[line_field] is not None:
                target_line = target_book_info[line_field]
                break
        
        # If we're dealing with a Points prop specifically, check for 'points' field too
        if target_line is None and 'points' in prop_type.lower():
            # Try additional fields that might contain the points line
            for points_field in ['points', 'playerTotal', 'pointsHandicap']:
                if points_field in target_book_info and target_book_info[points_field] is not None:
                    target_line = target_book_info[points_field]
                    break
        
        if target_odds is None or target_line is None:
            continue
            
        # Convert to float if it's a string
        if isinstance(target_odds, str):
            try:
                target_odds = float(target_odds)
            except:
                continue
                
        if isinstance(target_line, str):
            try:
                target_line = float(target_line)
            except:
                continue
        
        # Sanity check for points props - if line is very low, it might be wrong data
        if 'points' in prop_type.lower() and target_line < 10:
            # This is likely an error - NBA players rarely have point lines under 10
            continue
        
        target_american_odds = float(target_odds)
        target_decimal_odds = convert_american_to_decimal(target_american_odds)
        
        # Group bookmakers by line
        bookmakers_by_line = {}
        all_bookmakers_info = []
        
        for bookie, data in bookmaker_data.items():
            if bookie == target_bookmaker or not isinstance(data, dict) or not data.get('available', False):
                continue
            
            try:
                bookie_odds = data.get('odds', None)
                
                # FIXED: Get line with fallbacks for different field names in the JSON
                bookie_line = None
                for line_field in ['overUnder', 'line', 'total', 'value']:
                    if line_field in data and data[line_field] is not None:
                        bookie_line = data[line_field]
                        break
                
                # If we're dealing with a Points prop specifically, check for 'points' field too
                if bookie_line is None and 'points' in prop_type.lower():
                    # Try additional fields that might contain the points line
                    for points_field in ['points', 'playerTotal', 'pointsHandicap']:
                        if points_field in data and data[points_field] is not None:
                            bookie_line = data[points_field]
                            break
                
                if bookie_odds is None or bookie_line is None:
                    continue
                    
                # Convert to float if string
                if isinstance(bookie_odds, str):
                    bookie_odds = float(bookie_odds)
                    
                if isinstance(bookie_line, str):
                    bookie_line = float(bookie_line)
                
                # Sanity check for points props - if line is very low, it might be wrong data
                if 'points' in prop_type.lower() and bookie_line < 10:
                    # This is likely an error - NBA players rarely have point lines under 10
                    continue
                
                american_odds = float(bookie_odds)
                decimal_odds = convert_american_to_decimal(american_odds)
                
                if decimal_odds is not None:
                    bookie_info = {
                        'bookmaker': bookie,
                        'american_odds': american_odds,
                        'decimal_odds': decimal_odds,
                        'line': float(bookie_line)
                    }
                    
                    # Add to all bookmakers list for reference
                    all_bookmakers_info.append(bookie_info)
                    
                    # Round line to nearest 0.5 to group similar lines
                    rounded_line = round(float(bookie_line) * 2) / 2
                    
                    if rounded_line not in bookmakers_by_line:
                        bookmakers_by_line[rounded_line] = []
                        
                    bookmakers_by_line[rounded_line].append(bookie_info)
            except Exception as e:
                continue
        
        # Skip if no other bookmakers found
        if not bookmakers_by_line:
            continue
            
        # Create a string with all bookmaker lines for reference
        other_bookmakers_lines = []
        for bookie_info in sorted(all_bookmakers_info, key=lambda x: x['bookmaker']):
            other_bookmakers_lines.append(f"{bookie_info['bookmaker']}: {bookie_info['line']} @ {'+' if bookie_info['american_odds'] > 0 else ''}{int(bookie_info['american_odds'])}")
        
        other_lines_str = "; ".join(other_bookmakers_lines)
            
        # Find which line has the most bookmakers
        most_common_line = max(bookmakers_by_line.keys(), key=lambda x: len(bookmakers_by_line[x]))
        most_common_line_bookmakers = bookmakers_by_line[most_common_line]
        
        # For same line comparison, check if target line is close to the most common line
        target_rounded_line = round(float(target_line) * 2) / 2
        line_diff = abs(target_rounded_line - most_common_line)
        
        # If target line is similar to most common line
        if line_diff <= 0.5:
            # Calculate median odds for the most common line
            all_decimal_odds = [b['decimal_odds'] for b in most_common_line_bookmakers]
            all_american_odds = [b['american_odds'] for b in most_common_line_bookmakers]
            
            # Skip if not enough bookmakers for comparison
            if len(all_decimal_odds) < MIN_BOOKMAKERS_REQUIRED:
                continue
                
            median_decimal = np.median(all_decimal_odds)
            median_american = convert_decimal_to_american(median_decimal)
            
            # Check if odds difference is reasonable
            odds_diff = abs(target_american_odds - median_american)
            if odds_diff > MAX_ODDS_DIFFERENCE:
                outlier_count += 1
                continue
            
            # Find the bookmaker with odds closest to the median
            closest_idx = np.argmin([abs(b['decimal_odds'] - median_decimal) for b in most_common_line_bookmakers])
            closest_bookmaker = most_common_line_bookmakers[closest_idx]['bookmaker']
            
            # Calculate edge
            edge = calculate_edge(target_decimal_odds, median_decimal)
            
            if edge is not None and edge >= min_edge:
                valid_prop_count += 1
                results.append({
                    'player': player,
                    'prop_type': prop_type,
                    'line': target_line,
                    'direction': direction.upper(),
                    'target_bookmaker': target_bookmaker,
                    'target_odds': target_american_odds,
                    'median_bookmaker': f"median ({closest_bookmaker})",
                    'median_odds': median_american,
                    'edge': edge,
                    'num_bookmakers': len(most_common_line_bookmakers) + 1,
                    'comparison_type': 'same line comparison',
                    'other_bookmakers_lines': other_lines_str
                })
        else:
            # This is a line shopping opportunity, check if it's reasonable
            if target_rounded_line > (most_common_line + MAX_LINE_DIFFERENCE) or target_rounded_line < (most_common_line - MAX_LINE_DIFFERENCE):
                outlier_count += 1
                continue
                
            # For OVER props:
            # If target line < most common line, this is a value play for OVER
            if direction.upper() == 'OVER' and target_rounded_line < most_common_line:
                # Calculate median odds for the most common line (higher line)
                all_decimal_odds = [b['decimal_odds'] for b in most_common_line_bookmakers]
                
                # Skip if not enough bookmakers for comparison
                if len(all_decimal_odds) < MIN_BOOKMAKERS_REQUIRED:
                    continue
                    
                median_decimal = np.median(all_decimal_odds)
                median_american = convert_decimal_to_american(median_decimal)
                
                # Find the bookmaker with odds closest to the median
                closest_idx = np.argmin([abs(b['decimal_odds'] - median_decimal) for b in most_common_line_bookmakers])
                closest_bookmaker = most_common_line_bookmakers[closest_idx]['bookmaker']
                closest_line = most_common_line_bookmakers[closest_idx]['line']
                
                # Calculate line advantage
                line_advantage = closest_line - target_line
                
                # Check if the line difference is reasonable
                if line_advantage > MAX_LINE_DIFFERENCE:
                    outlier_count += 1
                    continue
                    
                # Calculate approximate edge based on line difference
                # Rule of thumb: each point is worth about 10% in equity
                line_edge = line_advantage * 10  # 10% per point difference
                
                if line_edge >= min_edge:
                    valid_prop_count += 1
                    results.append({
                        'player': player,
                        'prop_type': prop_type,
                        'line': target_line,
                        'direction': direction.upper(),
                        'target_bookmaker': target_bookmaker,
                        'target_odds': target_american_odds,
                        'compared_to': closest_bookmaker,
                        'compared_line': closest_line,
                        'compared_odds': median_american,
                        'median_bookmaker': closest_bookmaker,
                        'median_odds': median_american,
                        'line_diff': line_advantage,
                        'edge': line_edge,
                        'num_bookmakers': len(most_common_line_bookmakers) + 1,
                        'comparison_type': 'line shopping - OVER value',
                        'recommendation': 'BET OVER on lower line',
                        'other_bookmakers_lines': other_lines_str
                    })
            
            # For UNDER props:
            # If target line > most common line, this is a value play for UNDER
            elif direction.upper() == 'UNDER' and target_rounded_line > most_common_line:
                # Calculate median odds for the most common line (lower line)
                all_decimal_odds = [b['decimal_odds'] for b in most_common_line_bookmakers]
                
                # Skip if not enough bookmakers for comparison
                if len(all_decimal_odds) < MIN_BOOKMAKERS_REQUIRED:
                    continue
                    
                median_decimal = np.median(all_decimal_odds)
                median_american = convert_decimal_to_american(median_decimal)
                
                # Find the bookmaker with odds closest to the median
                closest_idx = np.argmin([abs(b['decimal_odds'] - median_decimal) for b in most_common_line_bookmakers])
                closest_bookmaker = most_common_line_bookmakers[closest_idx]['bookmaker']
                closest_line = most_common_line_bookmakers[closest_idx]['line']
                
                # Calculate line advantage
                line_advantage = target_line - closest_line
                
                # Check if the line difference is reasonable
                if line_advantage > MAX_LINE_DIFFERENCE:
                    outlier_count += 1
                    continue
                    
                # Calculate approximate edge based on line difference
                # Rule of thumb: each point is worth about 10% in equity
                line_edge = line_advantage * 10  # 10% per point difference
                
                if line_edge >= min_edge:
                    valid_prop_count += 1
                    results.append({
                        'player': player,
                        'prop_type': prop_type,
                        'line': target_line,
                        'direction': direction.upper(),
                        'target_bookmaker': target_bookmaker,
                        'target_odds': target_american_odds,
                        'compared_to': closest_bookmaker,
                        'compared_line': closest_line,
                        'compared_odds': median_american,
                        'median_bookmaker': closest_bookmaker,
                        'median_odds': median_american,
                        'line_diff': line_advantage,
                        'edge': line_edge,
                        'num_bookmakers': len(most_common_line_bookmakers) + 1,
                        'comparison_type': 'line shopping - UNDER value',
                        'recommendation': 'BET UNDER on higher line',
                        'other_bookmakers_lines': other_lines_str
                    })
    
    print(f"\nProcessed {processed_count} valid props with bookmaker data")
    print(f"Found {valid_prop_count} props with potential value")
    print(f"Filtered out {outlier_count} outlier props with unreasonable lines/odds")
    
    if not results:
        return pd.DataFrame()
    
    # Convert to DataFrame and sort by edge
    result_df = pd.DataFrame(results)
    
    # Calculate EV right after creating the DataFrame
    if 'target_odds' in result_df.columns and 'edge' in result_df.columns:
        result_df['implied_prob'] = result_df['target_odds'].apply(
            lambda x: calculate_implied_probability(convert_american_to_decimal(x))
        )
        result_df['ev_percentage'] = result_df.apply(
            lambda row: round((row['edge'] / 100) / row['implied_prob'] * 100, 2) 
            if pd.notna(row['implied_prob']) and row['implied_prob'] > 0 else 0, 
            axis=1
        )
    
    # Sort by EV percentage instead of edge
    result_df = result_df.sort_values('ev_percentage', ascending=False)
    
    return result_df

def analyze_csv_structure(csv_file: str) -> pd.DataFrame:
    """
    Analyze the structure of the CSV file and return a properly formatted DataFrame.
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        Properly formatted DataFrame
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} rows from {csv_file}")
        
        # Check if this is the raw props file from data_processing.py
        if 'byBookmaker' in df.columns:
            print("Detected raw props data format from data_processing.py")
            
            # Check a sample of the byBookmaker column to ensure it contains JSON data
            sample = df['byBookmaker'].dropna().iloc[0] if not df['byBookmaker'].dropna().empty else None
            
            if sample and isinstance(sample, str) and (sample.startswith('{') or sample.startswith('[')):
                # This looks like the correct format
                return df
            else:
                print("Warning: byBookmaker column doesn't contain JSON data")
                return df
        else:
            print("Warning: This does not appear to be the raw props data from data_processing.py")
            print("The script is designed to work with the raw props data that contains bookmaker JSON data")
            print("Available columns:")
            for col in df.columns:
                print(f"  - {col}")
            
            # Check if any column might contain JSON data
            for col in df.columns:
                sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if sample and isinstance(sample, str) and (sample.startswith('{') or sample.startswith('[')):
                    print(f"Found potential JSON data in column: {col}")
            
            return df
    except Exception as e:
        print(f"Error analyzing CSV structure: {e}")
        return None

def format_for_export(value_plays: pd.DataFrame) -> pd.DataFrame:
    """
    Format the value plays DataFrame for CSV export.
    
    Args:
        value_plays: DataFrame with value plays
        
    Returns:
        Formatted DataFrame ready for export
    """
    # Create a copy to avoid modifying the original
    export_df = value_plays.copy()
    
    # Calculate EV (Expected Value) based on edge and implied probability
    if 'edge' in export_df.columns and 'target_odds' in export_df.columns:
        export_df['implied_prob'] = export_df['target_odds'].apply(
            lambda x: calculate_implied_probability(convert_american_to_decimal(x))
        )
        export_df['ev_percentage'] = export_df.apply(
            lambda row: round((row['edge'] / 100) / row['implied_prob'] * 100, 2) if pd.notna(row['implied_prob']) and row['implied_prob'] > 0 else None, 
            axis=1
        )
        export_df['ev_formatted'] = export_df['ev_percentage'].apply(
            lambda x: f"{x:.2f}%" if pd.notna(x) else ""
        )
    
    # Format odds with + sign for positive American odds
    if 'target_odds' in export_df.columns:
        export_df['target_odds_formatted'] = export_df['target_odds'].apply(
            lambda x: f"+{int(x)}" if x > 0 else f"{int(x)}"
        )
    
    if 'median_odds' in export_df.columns:
        export_df['median_odds_formatted'] = export_df['median_odds'].apply(
            lambda x: f"+{int(x)}" if x > 0 else f"{int(x)}" if pd.notna(x) else ""
        )
        
    if 'compared_odds' in export_df.columns:
        export_df['compared_odds_formatted'] = export_df['compared_odds'].apply(
            lambda x: f"+{int(x)}" if x > 0 else f"{int(x)}" if pd.notna(x) else ""
        )
    
    # Format edge as percentage
    if 'edge' in export_df.columns:
        export_df['edge_formatted'] = export_df['edge'].apply(
            lambda x: f"{x:.2f}%"
        )
        
    # Format line differences
    if 'line_diff' in export_df.columns:
        export_df['line_diff_formatted'] = export_df['line_diff'].apply(
            lambda x: f"+{x:.1f}" if pd.notna(x) else ""
        )
    
    # Create a clear recommendation column
    if 'comparison_type' in export_df.columns:
        def get_recommendation(row):
            if 'line shopping' in row.get('comparison_type', ''):
                return row.get('recommendation', '')
            elif row.get('edge', 0) >= 3.0:
                return f"BET {row.get('direction', '')}"
            else:
                return "Consider betting"
                
        export_df['final_recommendation'] = export_df.apply(get_recommendation, axis=1)
    
    # Add a timestamp column as plain text
    from datetime import datetime
    export_df['export_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return export_df

def export_to_csv(value_plays: pd.DataFrame, target_bookmaker: str) -> str:
    """
    Export value plays to CSV file.
    
    Args:
        value_plays: DataFrame with value plays
        target_bookmaker: Name of the target bookmaker
        
    Returns:
        Path to the created CSV file
    """
    if value_plays.empty:
        print("No value plays to export.")
        return None
    
    # Format the DataFrame for export
    export_df = format_for_export(value_plays)
    
    # Generate filename with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"{target_bookmaker}_value_plays_{timestamp}.csv"
    
    try:
        # Export to CSV with text formatting
        export_df.to_csv(output_file, index=False, quoting=1)  # quoting=1 ensures all text fields are quoted
        print(f"Results successfully exported to {output_file}")
        return output_file
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        
        # Try alternative method if the first fails
        try:
            import os
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            alt_output_file = os.path.join(desktop_path, output_file)
            # Try export with maximum compatibility
            export_df.to_csv(alt_output_file, index=False, quoting=1, encoding='utf-8-sig')
            print(f"Results exported to desktop: {alt_output_file}")
            return alt_output_file
        except Exception as e2:
            print(f"Alternative export also failed: {e2}")
            return None

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Compare odds from a specific bookmaker against others.')
    parser.add_argument('--bookmaker', '-b', type=str, required=True, 
                        help='Target bookmaker name to analyze')
    parser.add_argument('--min-edge', '-e', type=float, default=2.0,
                        help='Minimum edge percentage to consider (default: 2.0)')
    parser.add_argument('--file', '-f', type=str, 
                        help='Specific props CSV file to analyze (default: most recent)')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Show debug information')
    parser.add_argument('--output', '-o', type=str, 
                        help='Output CSV file path (default: auto-generated)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed information for each prop')
    
    args = parser.parse_args()
    debug_mode = args.debug
    verbose_mode = args.verbose
    
    # Find props file to analyze
    if args.file:
        csv_file = args.file
    else:
        # Find the most recent props file from data_processing.py
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and f.startswith('nba_player_props') and not f.endswith('_enhanced_stats.csv')]
        
        if not csv_files:
            # Try looking for any CSV files
            csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and not f.endswith('_enhanced_stats.csv')]
            
        if not csv_files:
            print("No player props CSV files found.")
            return
        
        # Sort by modification time (most recent first)
        csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        csv_file = csv_files[0]
    
    print(f"Analyzing file: {csv_file}")
    print(f"Target bookmaker: {args.bookmaker}")
    print(f"Minimum edge: {args.min_edge}%")
    
    # Analyze CSV structure
    props_df = analyze_csv_structure(csv_file)
    
    if props_df is None or props_df.empty:
        print("Could not process the CSV file. Please check the format.")
        return
    
    if not debug_mode:
        # Suppress column info output
        pd.set_option('display.max_columns', None)
        
    # Get all available bookmakers
    available_bookmakers = extract_bookmaker_from_raw_props(props_df)
    
    if not available_bookmakers:
        print("No bookmakers found in the data. Please check the CSV format.")
        return
    
    if args.bookmaker not in available_bookmakers:
        print(f"Bookmaker '{args.bookmaker}' not found in the data. Available bookmakers:")
        for bookie in available_bookmakers:
            print(f"  - {bookie}")
        return
    
    # Find value plays using the raw props data
    value_plays = find_value_plays_raw(props_df, args.bookmaker, args.min_edge)
    
    if value_plays.empty:
        print(f"No value plays found for {args.bookmaker} with minimum edge of {args.min_edge}%")
        return
    
    # Categorize value plays
    same_line_plays = value_plays[value_plays['comparison_type'] == 'same line comparison'] if 'comparison_type' in value_plays.columns else pd.DataFrame()
    line_shopping_plays = value_plays[value_plays['comparison_type'].str.contains('line shopping', na=False)] if 'comparison_type' in value_plays.columns else pd.DataFrame()
    
    # Display summary information
    print(f"\nFound {len(value_plays)} value plays for {args.bookmaker}:")
    if not same_line_plays.empty:
        print(f"  - {len(same_line_plays)} plays with odds advantage (same line)")
    if not line_shopping_plays.empty:
        print(f"  - {len(line_shopping_plays)} plays with line shopping advantage")
    
    # Calculate some statistics
    if not value_plays.empty:
        avg_edge = value_plays['edge'].mean()
        max_edge = value_plays['edge'].max()
        min_edge = value_plays['edge'].min()
        
        # Distribution of bet directions
        direction_counts = value_plays['direction'].value_counts()
        
        # Print summary stats
        print(f"Average edge: {avg_edge:.2f}%")
        print(f"Edge range: {min_edge:.2f}% to {max_edge:.2f}%")
        
        print("\nDistribution by bet direction:")
        for direction, count in direction_counts.items():
            print(f"  {direction}: {count} props ({count/len(value_plays)*100:.1f}%)")
    
    # Only print detailed prop information in verbose mode
    if verbose_mode:
        print("\nDetailed value plays:")
        
        # First show line shopping opportunities
        if not line_shopping_plays.empty:
            print("\n=== LINE SHOPPING OPPORTUNITIES ===")
            for _, play in line_shopping_plays.iterrows():
                print(f"{play['player']} - {play['prop_type']} {play['direction']}")
                print(f"  {play['target_bookmaker']}: Line {play['line']}, Odds {'+' if play['target_odds'] > 0 else ''}{int(play['target_odds'])}")
                print(f"  {play['compared_to']}: Line {play['compared_line']}, Odds {'+' if play['compared_odds'] > 0 else ''}{int(play['compared_odds'])}")
                print(f"  Line Diff: {play['line_diff']:.1f}, Edge: {play['edge']:.2f}%")
                print(f"  Recommendation: {play['recommendation']}")
                print()
        
        # Then show odds advantage opportunities
        if not same_line_plays.empty:
            print("\n=== ODDS ADVANTAGE OPPORTUNITIES ===")
            for _, play in same_line_plays.iterrows():
                print(f"{play['player']} - {play['prop_type']} {play['line']} {play['direction']}")
                print(f"  {play['target_bookmaker']}: {'+' if play['target_odds'] > 0 else ''}{int(play['target_odds'])}")
                print(f"  {play['median_bookmaker']}: {'+' if play['median_odds'] > 0 else ''}{int(play['median_odds'])}")
                print(f"  Edge: {play['edge']:.2f}%")
                print(f"  Bookmakers: {play['num_bookmakers']}")
                print()
    
    # Export results to CSV
    output_file = args.output if args.output else None
    csv_path = export_to_csv(value_plays, args.bookmaker)
    
    print(f"\nAnalysis complete! Results exported to: {csv_path}")
    
    # Print top value plays sorted by EV instead of edge
    top_plays = value_plays.nlargest(5, 'ev_percentage')
    print("\nTOP 5 VALUE PLAYS BY EV:")
    for idx, play in top_plays.iterrows():
        if 'compared_to' in play and pd.notna(play['compared_to']):
            # Line shopping play
            print(f"{play['player']} - {play['prop_type']} {play['direction']} (Line: {play['line']})")
            print(f"  Compare to {play['compared_to']} (Line: {play['compared_line']})")
            print(f"  EV: {play.get('ev_percentage', 0):.2f}%, Edge: {play['edge']:.2f}%, Recommendation: {play.get('recommendation', '')}")
        else:
            # Same line play
            print(f"{play['player']} - {play['prop_type']} {play['line']} {play['direction']}")
            print(f"  {play['target_bookmaker']}: {'+' if play['target_odds'] > 0 else ''}{int(play['target_odds'])}")
            print(f"  EV: {play.get('ev_percentage', 0):.2f}%, Edge: {play['edge']:.2f}%")
        print()

if __name__ == "__main__":
    main()