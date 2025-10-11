#!/usr/bin/env python3
"""
Board Game Data Merger

This script merges the board game IDs from boardgame_ids.csv with the 
ranking data from boardgames_ranks.csv to create a comprehensive dataset.
"""

import csv
import pandas as pd

def merge_boardgame_data(ids_file, ranks_file, output_file):
    """Merge board game IDs with ranking data"""
    
    print("Board Game Data Merger")
    print("=" * 50)
    
    # Read the board game IDs file
    print(f"Reading board game IDs from: {ids_file}")
    try:
        ids_df = pd.read_csv(ids_file)
        print(f"✓ Loaded {len(ids_df)} games from your list")
    except Exception as e:
        print(f"Error reading {ids_file}: {str(e)}")
        return
    
    # Read the rankings file
    print(f"Reading rankings data from: {ranks_file}")
    try:
        ranks_df = pd.read_csv(ranks_file)
        print(f"✓ Loaded {len(ranks_df)} games from rankings database")
    except Exception as e:
        print(f"Error reading {ranks_file}: {str(e)}")
        return
    
    # Filter out games without BGG IDs
    valid_ids = ids_df[ids_df['bgg_id'].notna() & (ids_df['bgg_id'] != '')]
    print(f"✓ Found {len(valid_ids)} games with valid BGG IDs")
    
    # Convert BGG IDs to integers for matching
    valid_ids = valid_ids.copy()
    valid_ids['bgg_id'] = pd.to_numeric(valid_ids['bgg_id'], errors='coerce')
    valid_ids = valid_ids[valid_ids['bgg_id'].notna()]
    
    # Merge the datasets on BGG ID
    print("\nMerging datasets...")
    merged_df = pd.merge(
        valid_ids, 
        ranks_df, 
        left_on='bgg_id', 
        right_on='id', 
        how='left'
    )
    
    # Count matches
    matched_games = merged_df[merged_df['id'].notna()]
    unmatched_games = merged_df[merged_df['id'].isna()]
    
    print(f"✓ Successfully matched {len(matched_games)} games")
    print(f"✗ Could not find ranking data for {len(unmatched_games)} games")
    
    # Reorganize columns for better readability
    column_order = [
        'original_line',
        'game_name', 
        'bgg_id',
        'name',  # BGG official name
        'yearpublished',
        'rank',
        'bayesaverage',
        'average',
        'usersrated',
        'is_expansion',
        'abstracts_rank',
        'cgs_rank', 
        'childrensgames_rank',
        'familygames_rank',
        'partygames_rank',
        'strategygames_rank',
        'thematic_rank',
        'wargames_rank',
        'status'
    ]
    
    # Select and reorder columns
    available_columns = [col for col in column_order if col in merged_df.columns]
    final_df = merged_df[available_columns]
    
    # Sort by BGG rank (putting unranked games at the end)
    final_df['rank_sort'] = pd.to_numeric(final_df['rank'], errors='coerce')
    final_df = final_df.sort_values('rank_sort', na_position='last')
    final_df = final_df.drop('rank_sort', axis=1)
    
    # Save the merged data
    print(f"\nSaving merged data to: {output_file}")
    try:
        final_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✓ Successfully saved {len(final_df)} games to {output_file}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        return
    
    # Print summary statistics
    print("\n" + "=" * 50)
    print("SUMMARY STATISTICS")
    print("=" * 50)
    
    print(f"Total games in your list: {len(ids_df)}")
    print(f"Games with BGG IDs: {len(valid_ids)}")
    print(f"Games matched with ranking data: {len(matched_games)}")
    print(f"Games without ranking data: {len(unmatched_games)}")
    
    if len(matched_games) > 0:
        ranked_games = matched_games[matched_games['rank'].notna()]
        print(f"Games with BGG ranks: {len(ranked_games)}")
        
        if len(ranked_games) > 0:
            best_rank = ranked_games['rank'].min()
            worst_rank = ranked_games['rank'].max()
            avg_rank = ranked_games['rank'].mean()
            
            print(f"\nRanking Statistics:")
            print(f"  Best rank: #{int(best_rank)}")
            print(f"  Worst rank: #{int(worst_rank)}")
            print(f"  Average rank: #{avg_rank:.1f}")
            
            # Show top 10 ranked games from your collection
            top_games = ranked_games.nsmallest(10, 'rank')
            print(f"\nTop 10 ranked games in your collection:")
            for i, (_, game) in enumerate(top_games.iterrows(), 1):
                game_name = game['name'] if pd.notna(game['name']) else game['game_name']
                print(f"  {i:2d}. #{int(game['rank']):4d} - {game_name}")
    
    # Show unmatched games
    if len(unmatched_games) > 0:
        print(f"\nGames without ranking data:")
        for _, game in unmatched_games.iterrows():
            print(f"  - {game['game_name']} (ID: {int(game['bgg_id'])})")
    
    print(f"\n✓ Merge complete! Results saved to: {output_file}")

def main():
    """Main function"""
    ids_file = "boardgame_ids.csv"
    ranks_file = "boardgames_ranks.csv"
    output_file = "merged_boardgames.csv"
    
    # Check if pandas is available
    try:
        import pandas as pd
    except ImportError:
        print("Error: pandas module not found!")
        print("Please install it with: pip install pandas")
        return
    
    merge_boardgame_data(ids_file, ranks_file, output_file)

if __name__ == "__main__":
    main()