#!/usr/bin/env python3
"""
Enhanced Board Game Analysis

This script provides better analysis of the merged board game data,
separating ranked games from unranked ones and providing more detailed statistics.
"""

import pandas as pd

def analyze_merged_data(input_file):
    """Analyze the merged board game data"""
    
    print("Enhanced Board Game Analysis")
    print("=" * 60)
    
    try:
        df = pd.read_csv(input_file)
        print(f"✓ Loaded {len(df)} games from {input_file}")
    except Exception as e:
        print(f"Error reading {input_file}: {str(e)}")
        return
    
    # Separate ranked and unranked games
    ranked_games = df[(df['rank'] > 0) & (df['rank'].notna())]
    unranked_games = df[(df['rank'] == 0) | (df['rank'].isna())]
    expansions = df[df['is_expansion'] == 1]
    base_games = df[df['is_expansion'] == 0]
    
    print(f"\n📊 COLLECTION OVERVIEW")
    print(f"├─ Total games: {len(df)}")
    print(f"├─ Base games: {len(base_games)}")
    print(f"├─ Expansions: {len(expansions)}")
    print(f"├─ BGG ranked games: {len(ranked_games)}")
    print(f"└─ Unranked/New games: {len(unranked_games)}")
    
    if len(ranked_games) > 0:
        print(f"\n🏆 RANKING STATISTICS")
        best_rank = int(ranked_games['rank'].min())
        worst_rank = int(ranked_games['rank'].max())
        avg_rank = ranked_games['rank'].mean()
        median_rank = ranked_games['rank'].median()
        
        print(f"├─ Best rank: #{best_rank}")
        print(f"├─ Worst rank: #{worst_rank}")
        print(f"├─ Average rank: #{avg_rank:.1f}")
        print(f"└─ Median rank: #{median_rank:.1f}")
        
        # Top ranked games in collection
        print(f"\n🌟 TOP 15 RANKED GAMES IN YOUR COLLECTION")
        top_ranked = ranked_games.nsmallest(15, 'rank')
        for i, (_, game) in enumerate(top_ranked.iterrows(), 1):
            game_name = game['name'] if pd.notna(game['name']) else game['game_name']
            year = f"({int(game['yearpublished'])})" if pd.notna(game['yearpublished']) else ""
            rating = f"{game['bayesaverage']:.2f}" if pd.notna(game['bayesaverage']) else "N/A"
            print(f"{i:2d}. #{int(game['rank']):4d} - {game_name} {year} - Rating: {rating}")
        
        # Rating analysis
        rated_games = ranked_games[ranked_games['bayesaverage'] > 0]
        if len(rated_games) > 0:
            print(f"\n⭐ RATING ANALYSIS ({len(rated_games)} rated games)")
            avg_rating = rated_games['bayesaverage'].mean()
            best_rating = rated_games['bayesaverage'].max()
            worst_rating = rated_games['bayesaverage'].min()
            
            print(f"├─ Average rating: {avg_rating:.2f}")
            print(f"├─ Best rating: {best_rating:.2f}")
            print(f"└─ Lowest rating: {worst_rating:.2f}")
            
            # Rating distribution
            excellent = len(rated_games[rated_games['bayesaverage'] >= 8.0])
            very_good = len(rated_games[(rated_games['bayesaverage'] >= 7.5) & (rated_games['bayesaverage'] < 8.0)])
            good = len(rated_games[(rated_games['bayesaverage'] >= 7.0) & (rated_games['bayesaverage'] < 7.5)])
            average = len(rated_games[(rated_games['bayesaverage'] >= 6.5) & (rated_games['bayesaverage'] < 7.0)])
            below_avg = len(rated_games[rated_games['bayesaverage'] < 6.5])
            
            print(f"\n📈 RATING DISTRIBUTION")
            print(f"├─ Excellent (8.0+): {excellent} games")
            print(f"├─ Very Good (7.5-7.9): {very_good} games")
            print(f"├─ Good (7.0-7.4): {good} games")
            print(f"├─ Average (6.5-6.9): {average} games")
            print(f"└─ Below Average (<6.5): {below_avg} games")
    
    # Show recent games
    recent_games = df[df['yearpublished'] >= 2020]
    if len(recent_games) > 0:
        print(f"\n🆕 RECENT GAMES (2020+): {len(recent_games)} games")
        recent_sorted = recent_games.sort_values('yearpublished', ascending=False)
        for i, (_, game) in enumerate(recent_sorted.head(10).iterrows(), 1):
            game_name = game['name'] if pd.notna(game['name']) else game['game_name']
            year = int(game['yearpublished']) if pd.notna(game['yearpublished']) else "Unknown"
            rank_str = f"#{int(game['rank'])}" if pd.notna(game['rank']) and game['rank'] > 0 else "Unranked"
            print(f"{i:2d}. {game_name} ({year}) - {rank_str}")
    
    # Show unranked games
    if len(unranked_games) > 0:
        print(f"\n❓ UNRANKED/NEW GAMES: {len(unranked_games)} games")
        for i, (_, game) in enumerate(unranked_games.head(10).iterrows(), 1):
            game_name = game['name'] if pd.notna(game['name']) else game['game_name']
            year = f"({int(game['yearpublished'])})" if pd.notna(game['yearpublished']) else ""
            exp_marker = " [Expansion]" if game['is_expansion'] == 1 else ""
            print(f"{i:2d}. {game_name} {year}{exp_marker}")
        
        if len(unranked_games) > 10:
            print(f"    ... and {len(unranked_games) - 10} more")
    
    # Create a cleaned CSV with better sorting
    print(f"\n💾 CREATING CLEAN ANALYSIS FILE")
    
    # Sort: ranked games first (by rank), then unranked games
    df_sorted = pd.concat([
        ranked_games.sort_values('rank'),
        unranked_games.sort_values(['is_expansion', 'yearpublished'], ascending=[True, False])
    ], ignore_index=True)
    
    # Add some computed columns
    df_sorted['rating_category'] = df_sorted['bayesaverage'].apply(lambda x: 
        'Excellent (8.0+)' if pd.notna(x) and x >= 8.0 else
        'Very Good (7.5-7.9)' if pd.notna(x) and x >= 7.5 else
        'Good (7.0-7.4)' if pd.notna(x) and x >= 7.0 else
        'Average (6.5-6.9)' if pd.notna(x) and x >= 6.5 else
        'Below Average (<6.5)' if pd.notna(x) and x > 0 else
        'Not Rated'
    )
    
    df_sorted['game_type'] = df_sorted['is_expansion'].apply(lambda x: 'Expansion' if x == 1 else 'Base Game')
    df_sorted['rank_display'] = df_sorted['rank'].apply(lambda x: f"#{int(x)}" if pd.notna(x) and x > 0 else "Unranked")
    
    output_file = "boardgames_analysis.csv"
    df_sorted.to_csv(output_file, index=False, encoding='utf-8')
    print(f"✓ Saved detailed analysis to: {output_file}")
    
    print(f"\n🎯 COLLECTION QUALITY SUMMARY")
    if len(ranked_games) > 0:
        top_1000 = len(ranked_games[ranked_games['rank'] <= 1000])
        top_500 = len(ranked_games[ranked_games['rank'] <= 500])
        top_100 = len(ranked_games[ranked_games['rank'] <= 100])
        
        print(f"├─ Games in BGG Top 100: {top_100}")
        print(f"├─ Games in BGG Top 500: {top_500}")
        print(f"├─ Games in BGG Top 1000: {top_1000}")
        
        if len(rated_games) > 0:
            high_rated = len(rated_games[rated_games['bayesaverage'] >= 7.5])
            print(f"└─ Highly rated games (7.5+): {high_rated}")
    
    print(f"\n✅ Analysis complete!")

def main():
    """Main function"""
    input_file = "merged_boardgames.csv"
    
    try:
        import pandas as pd
    except ImportError:
        print("Error: pandas module not found!")
        return
    
    analyze_merged_data(input_file)

if __name__ == "__main__":
    main()