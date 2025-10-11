#!/usr/bin/env python3
"""
Enhance Board Game Collection with BGG Details

This script fetches additional information from BoardGameGeek for each game:
- Best player count (community votes)
- Recommended player count (community votes) 
- Playing time (min and max)
- Complexity weight (1-5 scale)
- Game mechanics and categories

Updates the existing CSV with this enhanced data.
"""

import pandas as pd
import requests
import xml.etree.ElementTree as ET
import time
import sys
from datetime import datetime

def fetch_bgg_game_details(bgg_id):
    """
    Fetch detailed game information from BGG API
    Returns dict with player counts, playing time, weight, etc.
    """
    if pd.isna(bgg_id):
        return None
    
    bgg_id = int(bgg_id)
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={bgg_id}&stats=1"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        item = root.find('.//item')
        
        if item is None:
            return None
        
        details = {
            'minplayers': None,
            'maxplayers': None,
            'best_player_count': [],
            'recommended_player_count': [],
            'minplaytime': None,
            'maxplaytime': None,
            'complexity_weight': None,
            'mechanics': [],
            'categories': []
        }
        
        # Basic player count and time info
        minplayers = item.find('.//minplayers')
        if minplayers is not None:
            details['minplayers'] = minplayers.get('value')
        
        maxplayers = item.find('.//maxplayers')
        if maxplayers is not None:
            details['maxplayers'] = maxplayers.get('value')
        
        minplaytime = item.find('.//minplaytime')
        if minplaytime is not None:
            details['minplaytime'] = minplaytime.get('value')
        
        maxplaytime = item.find('.//maxplaytime')
        if maxplaytime is not None:
            details['maxplaytime'] = maxplaytime.get('value')
        
        # Complexity weight
        statistics = item.find('.//statistics')
        if statistics is not None:
            averageweight = statistics.find('.//averageweight')
            if averageweight is not None:
                weight = averageweight.get('value')
                if weight and weight != '0':
                    details['complexity_weight'] = round(float(weight), 2)
        
        # Player count polls (best and recommended)
        polls = item.findall('.//poll')
        for poll in polls:
            if poll.get('name') == 'suggested_numplayers':
                results = poll.findall('.//results')
                for result in results:
                    numplayers = result.get('numplayers')
                    if numplayers and numplayers != '':
                        best_votes = 0
                        recommended_votes = 0
                        not_recommended_votes = 0
                        
                        for res in result.findall('.//result'):
                            value = res.get('value')
                            votes = int(res.get('numvotes', 0))
                            
                            if value == 'Best':
                                best_votes = votes
                            elif value == 'Recommended':
                                recommended_votes = votes
                            elif value == 'Not Recommended':
                                not_recommended_votes = votes
                        
                        total_votes = best_votes + recommended_votes + not_recommended_votes
                        if total_votes > 5:  # Only consider if enough votes
                            # Best: more than 50% voted "Best"
                            if best_votes > (total_votes * 0.5):
                                details['best_player_count'].append(numplayers)
                            # Recommended: "Best" + "Recommended" > 60%
                            elif (best_votes + recommended_votes) > (total_votes * 0.6):
                                details['recommended_player_count'].append(numplayers)
        
        # Game mechanics
        links = item.findall('.//link')
        for link in links:
            link_type = link.get('type')
            if link_type == 'boardgamemechanic':
                details['mechanics'].append(link.get('value'))
            elif link_type == 'boardgamecategory':
                details['categories'].append(link.get('value'))
        
        return details
        
    except Exception as e:
        print(f"❌ Error fetching BGG data for ID {bgg_id}: {e}")
        return None

def format_player_counts(player_list):
    """Format player count list into a readable string"""
    if not player_list:
        return ""
    
    # Convert to integers for sorting, handle special cases
    nums = []
    specials = []
    
    for p in player_list:
        if p.isdigit():
            nums.append(int(p))
        else:
            specials.append(p)  # e.g., "8+"
    
    nums.sort()
    result = [str(n) for n in nums] + specials
    return ", ".join(result)

def format_playtime(min_time, max_time):
    """Format playing time into a readable string"""
    if not min_time and not max_time:
        return ""
    
    min_time = int(min_time) if min_time and min_time != '0' else None
    max_time = int(max_time) if max_time and max_time != '0' else None
    
    if min_time and max_time:
        if min_time == max_time:
            return f"{min_time} min"
        else:
            return f"{min_time}-{max_time} min"
    elif max_time:
        return f"{max_time} min"
    elif min_time:
        return f"{min_time} min"
    else:
        return ""

def enhance_csv_with_bgg_details():
    """Main function to enhance the CSV with BGG details"""
    
    print("🎲 Enhancing Board Game Collection with BGG Details")
    print("=" * 55)
    
    # Read the current CSV
    try:
        df = pd.read_csv('brett_spiele.csv')
        print(f"✓ Loaded {len(df)} games from brett_spiele.csv")
    except FileNotFoundError:
        print("❌ brett_spiele.csv not found!")
        return
    
    # Add new columns for enhanced data
    new_columns = [
        'min_players',
        'max_players', 
        'best_player_count',
        'recommended_player_count',
        'playing_time',
        'complexity_weight',
        'mechanics',
        'categories'
    ]
    
    for col in new_columns:
        if col not in df.columns:
            df[col] = ""
    
    # Track progress
    total_games = len(df)
    games_processed = 0
    games_enhanced = 0
    games_skipped = 0
    
    print(f"\n🚀 Starting to fetch BGG details for {total_games} games...")
    print("⏱️  This will take several minutes due to API rate limiting (2-3 seconds per game)")
    
    for index, row in df.iterrows():
        games_processed += 1
        bgg_id = row['bgg_id']
        game_name = row['game_name']
        
        print(f"\n[{games_processed}/{total_games}] 🎯 {game_name}")
        
        # Skip if already has detailed data
        if pd.notna(row.get('complexity_weight')) and row.get('complexity_weight') != "":
            print("   ⏭️  Already has detailed data, skipping")
            games_skipped += 1
            continue
        
        # Fetch BGG details
        details = fetch_bgg_game_details(bgg_id)
        
        if details:
            # Update the row with fetched details
            df.at[index, 'min_players'] = details['minplayers'] or ""
            df.at[index, 'max_players'] = details['maxplayers'] or ""
            df.at[index, 'best_player_count'] = format_player_counts(details['best_player_count'])
            df.at[index, 'recommended_player_count'] = format_player_counts(details['recommended_player_count'])
            df.at[index, 'playing_time'] = format_playtime(details['minplaytime'], details['maxplaytime'])
            df.at[index, 'complexity_weight'] = details['complexity_weight'] or ""
            df.at[index, 'mechanics'] = "; ".join(details['mechanics'][:5])  # Limit to top 5
            df.at[index, 'categories'] = "; ".join(details['categories'][:3])  # Limit to top 3
            
            print(f"   ✓ Players: {details['minplayers']}-{details['maxplayers']}")
            print(f"   ✓ Best: {format_player_counts(details['best_player_count'])}")
            print(f"   ✓ Time: {format_playtime(details['minplaytime'], details['maxplaytime'])}")
            print(f"   ✓ Weight: {details['complexity_weight']}")
            
            games_enhanced += 1
            
            # Save progress every 10 games
            if games_processed % 10 == 0:
                backup_filename = f'brett_spiele_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                df.to_csv(backup_filename, index=False)
                print(f"   💾 Progress saved to {backup_filename}")
        else:
            print("   ❌ Failed to fetch details")
        
        # Rate limiting - be respectful to BGG
        print("   ⏳ Waiting 2.5 seconds...")
        time.sleep(2.5)
    
    # Save the enhanced CSV
    output_filename = 'brett_spiele_enhanced.csv'
    df.to_csv(output_filename, index=False)
    
    print(f"\n🎉 ENHANCEMENT COMPLETE!")
    print("=" * 30)
    print(f"✅ Games processed: {games_processed}")
    print(f"✅ Games enhanced: {games_enhanced}")
    print(f"⏭️  Games skipped: {games_skipped}")
    print(f"💾 Enhanced data saved to: {output_filename}")
    
    # Show some sample enhanced data
    enhanced_games = df[df['complexity_weight'] != ""].head(3)
    if not enhanced_games.empty:
        print(f"\n📊 Sample Enhanced Games:")
        for _, game in enhanced_games.iterrows():
            print(f"   🎲 {game['game_name']}")
            print(f"      Players: {game['min_players']}-{game['max_players']}")
            print(f"      Best: {game['best_player_count']}")
            print(f"      Time: {game['playing_time']}")
            print(f"      Weight: {game['complexity_weight']}/5")

if __name__ == "__main__":
    enhance_csv_with_bgg_details()