#!/usr/bin/env python3
"""
Step 2: Build Complete Board Game Collection

This script takes the BGG IDs from step 1 and creates a complete collection:
1. Matches with BGG ranking data (boardgames_ranks.csv)
2. Downloads game images from BGG
3. Fetches detailed BGG information (player counts, complexity, etc.)
4. Creates the final enhanced CSV and HTML webpage

Input: boardgame_ids.csv (from step 1)
Output: Complete board game collection website
"""

import pandas as pd
import requests
import xml.etree.ElementTree as ET
import time
import os
import sys
from datetime import datetime
from urllib.parse import quote
import shutil

def load_bgg_ids():
    """Load the BGG IDs from step 1"""
    try:
        df = pd.read_csv('boardgame_ids.csv')
        # Filter out games without BGG IDs
        df = df[df['bgg_id'].notna() & (df['bgg_id'] != '')]
        df['bgg_id'] = df['bgg_id'].astype(int)
        print(f"✓ Loaded {len(df)} games with BGG IDs")
        return df
    except FileNotFoundError:
        print("❌ boardgame_ids.csv not found! Run step1_extract_ids.py first.")
        return None

def merge_with_ranking_data(ids_df):
    """Merge with BGG ranking data if available"""
    print("\n📊 Merging with BGG ranking data...")
    
    try:
        ranks_df = pd.read_csv('boardgames_ranks.csv')
        print(f"✓ Loaded {len(ranks_df)} games from ranking database")
        
        # Merge on BGG ID
        merged_df = ids_df.merge(
            ranks_df, 
            left_on='bgg_id', 
            right_on='id', 
            how='left'
        )
        
        # Fill missing values
        merged_df['rank'] = merged_df['rank'].fillna(999999)
        merged_df['bayesaverage'] = merged_df['bayesaverage'].fillna(0)
        merged_df['name'] = merged_df['name'].fillna(merged_df['matched_name'])
        
        print(f"✓ Merged data for {len(merged_df)} games")
        matched_with_ranks = len(merged_df[merged_df['rank'] != 999999])
        print(f"✓ Found ranking data for {matched_with_ranks} games")
        
        return merged_df
        
    except FileNotFoundError:
        print("⚠️  boardgames_ranks.csv not found, continuing without ranking data")
        # Create minimal structure
        ids_df['rank'] = 999999
        ids_df['bayesaverage'] = 0
        ids_df['average'] = 0
        ids_df['usersrated'] = 0
        ids_df['is_expansion'] = 0
        ids_df['name'] = ids_df['matched_name']
        return ids_df

def download_game_image(bgg_id, game_name):
    """Download a single game image from BGG"""
    try:
        # Get game details to find image URL
        url = f"https://boardgamegeek.com/xmlapi2/thing?id={bgg_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        item = root.find('.//item')
        
        if item is None:
            return 'NO_GAME_DATA'
        
        # Find image URL
        image_elem = item.find('.//image')
        if image_elem is None or not image_elem.text:
            return 'NO_IMAGE'
        
        image_url = image_elem.text
        
        # Create safe filename
        safe_name = "".join(c for c in game_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        year_elem = item.find('.//yearpublished')
        year = year_elem.get('value') if year_elem is not None else '0000'
        
        # Determine file extension
        if image_url.lower().endswith('.png'):
            ext = '.png'
        else:
            ext = '.jpg'
        
        filename = f"{safe_name}_{year}_{bgg_id}{ext}"
        filepath = os.path.join('images', filename)
        
        # Download image
        img_response = requests.get(image_url, timeout=15)
        img_response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(img_response.content)
        
        return filename
        
    except Exception as e:
        print(f"❌ Error downloading image for {game_name}: {e}")
        return 'DOWNLOAD_FAILED'

def download_all_images(df):
    """Download images for all games"""
    print("\n🖼️  Downloading game images...")
    
    # Create images directory
    if not os.path.exists('images'):
        os.makedirs('images')
        print("✓ Created images directory")
    
    total_games = len(df)
    successful_downloads = 0
    
    for index, row in df.iterrows():
        game_num = index + 1
        bgg_id = row['bgg_id']
        game_name = row['matched_name'] or row['game_name']
        
        print(f"[{game_num}/{total_games}] 📸 {game_name}")
        
        # Check if image already exists
        existing_images = [f for f in os.listdir('images') if f.startswith(f"{game_name}_{row.get('year', '')}")[:10]]
        if existing_images:
            df.at[index, 'image_filename'] = existing_images[0]
            print(f"   ✓ Image already exists: {existing_images[0]}")
            successful_downloads += 1
            continue
        
        # Download image
        filename = download_game_image(bgg_id, game_name)
        df.at[index, 'image_filename'] = filename
        
        if filename not in ['NO_GAME_DATA', 'NO_IMAGE', 'DOWNLOAD_FAILED']:
            print(f"   ✓ Downloaded: {filename}")
            successful_downloads += 1
        else:
            print(f"   ❌ Failed: {filename}")
        
        # Rate limiting
        time.sleep(2)
    
    print(f"\n✅ Image download complete: {successful_downloads}/{total_games} successful")
    return df

def fetch_detailed_bgg_info(bgg_id):
    """Fetch detailed game information from BGG"""
    try:
        url = f"https://boardgamegeek.com/xmlapi2/thing?id={bgg_id}&stats=1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        item = root.find('.//item')
        
        if item is None:
            return {}
        
        details = {
            'min_players': '',
            'max_players': '',
            'best_player_count': '',
            'recommended_player_count': '',
            'playing_time': '',
            'complexity_weight': '',
            'mechanics': '',
            'categories': ''
        }
        
        # Basic info
        minplayers = item.find('.//minplayers')
        if minplayers is not None:
            details['min_players'] = minplayers.get('value', '')
        
        maxplayers = item.find('.//maxplayers')
        if maxplayers is not None:
            details['max_players'] = maxplayers.get('value', '')
        
        minplaytime = item.find('.//minplaytime')
        maxplaytime = item.find('.//maxplaytime')
        
        if minplaytime is not None and maxplaytime is not None:
            min_time = minplaytime.get('value', '0')
            max_time = maxplaytime.get('value', '0')
            if min_time != '0' or max_time != '0':
                if min_time == max_time and min_time != '0':
                    details['playing_time'] = f"{min_time} min"
                elif min_time != '0' and max_time != '0':
                    details['playing_time'] = f"{min_time}-{max_time} min"
                elif max_time != '0':
                    details['playing_time'] = f"{max_time} min"
        
        # Complexity weight
        statistics = item.find('.//statistics')
        if statistics is not None:
            averageweight = statistics.find('.//averageweight')
            if averageweight is not None:
                weight = averageweight.get('value', '')
                if weight and weight != '0':
                    details['complexity_weight'] = str(round(float(weight), 2))
        
        # Player count recommendations
        polls = item.findall('.//poll')
        best_counts = []
        recommended_counts = []
        
        for poll in polls:
            if poll.get('name') == 'suggested_numplayers':
                results = poll.findall('.//results')
                for result in results:
                    numplayers = result.get('numplayers', '')
                    if numplayers:
                        best_votes = 0
                        recommended_votes = 0
                        not_recommended_votes = 0
                        
                        for res in result.findall('.//result'):
                            value = res.get('value', '')
                            votes = int(res.get('numvotes', 0))
                            
                            if value == 'Best':
                                best_votes = votes
                            elif value == 'Recommended':
                                recommended_votes = votes
                            elif value == 'Not Recommended':
                                not_recommended_votes = votes
                        
                        total_votes = best_votes + recommended_votes + not_recommended_votes
                        if total_votes > 5:
                            if best_votes > (total_votes * 0.5):
                                best_counts.append(numplayers)
                            elif (best_votes + recommended_votes) > (total_votes * 0.6):
                                recommended_counts.append(numplayers)
        
        details['best_player_count'] = ', '.join(sorted(best_counts, key=lambda x: int(x) if x.isdigit() else 999))
        details['recommended_player_count'] = ', '.join(sorted(recommended_counts, key=lambda x: int(x) if x.isdigit() else 999))
        
        # Mechanics and categories
        links = item.findall('.//link')
        mechanics = []
        categories = []
        
        for link in links:
            link_type = link.get('type', '')
            if link_type == 'boardgamemechanic':
                mechanics.append(link.get('value', ''))
            elif link_type == 'boardgamecategory':
                categories.append(link.get('value', ''))
        
        details['mechanics'] = '; '.join(mechanics[:5])  # Top 5 mechanics
        details['categories'] = '; '.join(categories[:3])  # Top 3 categories
        
        return details
        
    except Exception as e:
        print(f"❌ Error fetching details for ID {bgg_id}: {e}")
        return {}

def enhance_with_detailed_info(df):
    """Add detailed BGG information to all games"""
    print("\n🎯 Fetching detailed BGG information...")
    
    total_games = len(df)
    enhanced_count = 0
    
    # Add columns for enhanced data
    detail_columns = [
        'min_players', 'max_players', 'best_player_count', 
        'recommended_player_count', 'playing_time', 'complexity_weight',
        'mechanics', 'categories'
    ]
    
    for col in detail_columns:
        if col not in df.columns:
            df[col] = ''
    
    for index, row in df.iterrows():
        game_num = index + 1
        bgg_id = row['bgg_id']
        game_name = row['matched_name'] or row['game_name']
        
        print(f"[{game_num}/{total_games}] 🎯 {game_name}")
        
        # Skip if already has detailed data
        if pd.notna(row.get('complexity_weight')) and row.get('complexity_weight') != '':
            print("   ⏭️  Already has detailed data, skipping")
            enhanced_count += 1
            continue
        
        # Fetch detailed info
        details = fetch_detailed_bgg_info(bgg_id)
        
        if details:
            for key, value in details.items():
                df.at[index, key] = value
            
            print(f"   ✓ Enhanced with BGG details")
            enhanced_count += 1
        else:
            print(f"   ❌ Failed to get details")
        
        # Rate limiting
        time.sleep(2.5)
    
    print(f"\n✅ Enhancement complete: {enhanced_count}/{total_games} games enhanced")
    return df

def create_final_csv(df):
    """Create the final enhanced CSV file"""
    print("\n💾 Creating final CSV file...")
    
    # Clean up and organize columns
    final_columns = [
        'original_line', 'game_name', 'bgg_id', 'name', 'year', 'yearpublished',
        'rank', 'bayesaverage', 'average', 'usersrated', 'is_expansion',
        'status', 'confidence', 'image_filename',
        'min_players', 'max_players', 'best_player_count', 'recommended_player_count',
        'playing_time', 'complexity_weight', 'mechanics', 'categories'
    ]
    
    # Add missing columns with default values
    for col in final_columns:
        if col not in df.columns:
            df[col] = ''
    
    # Reorder columns
    df_final = df[final_columns].copy()
    
    # Clean up year data
    if 'yearpublished' not in df_final.columns or df_final['yearpublished'].isna().all():
        df_final['yearpublished'] = df_final['year']
    
    # Save final CSV
    filename = 'brett_spiele_enhanced.csv'
    df_final.to_csv(filename, index=False)
    
    print(f"✓ Final collection saved to: {filename}")
    print(f"✓ Total games: {len(df_final)}")
    print(f"✓ Games with images: {len(df_final[~df_final['image_filename'].isin(['NO_IMAGE', 'DOWNLOAD_FAILED', ''])])}")
    print(f"✓ Games with detailed info: {len(df_final[df_final['complexity_weight'] != ''])}")
    
    return df_final

def update_html_file():
    """Update the HTML file to use the new CSV"""
    print("\n🌐 Updating HTML webpage...")
    
    html_file = 'board_games_collection.html'
    if os.path.exists(html_file):
        print(f"✓ HTML file already configured for brett_spiele_enhanced.csv")
    else:
        print("⚠️  board_games_collection.html not found - you'll need to create the webpage")
    
    return True

def cleanup_old_files():
    """Clean up old intermediate files"""
    print("\n🧹 Cleaning up old files...")
    
    # Files that are no longer needed
    old_files = [
        'extract_boardgame_ids_improved.py',
        'merge_boardgames.py',
        'download_images.py',
        'analyze_collection.py',
        'enhance_with_bgg_details.py',
        'merged_boardgames.csv'
    ]
    
    cleaned_count = 0
    for filename in old_files:
        if os.path.exists(filename):
            try:
                # Move to archive instead of deleting
                archive_dir = 'archive_dev_scripts'
                if not os.path.exists(archive_dir):
                    os.makedirs(archive_dir)
                
                if not os.path.exists(os.path.join(archive_dir, filename)):
                    shutil.move(filename, os.path.join(archive_dir, filename))
                    print(f"✓ Archived: {filename}")
                    cleaned_count += 1
                else:
                    os.remove(filename)
                    print(f"✓ Removed: {filename}")
                    cleaned_count += 1
            except Exception as e:
                print(f"❌ Error cleaning {filename}: {e}")
    
    print(f"✓ Cleaned up {cleaned_count} old files")

def main():
    """Main function - Build complete board game collection"""
    
    print("🎲 Build Board Game Collection - Step 2")
    print("=" * 50)
    
    # Load BGG IDs from step 1
    ids_df = load_bgg_ids()
    if ids_df is None:
        return
    
    # Step 1: Merge with ranking data
    merged_df = merge_with_ranking_data(ids_df)
    
    # Step 2: Download images
    images_df = download_all_images(merged_df)
    
    # Step 3: Enhance with detailed BGG info
    enhanced_df = enhance_with_detailed_info(images_df)
    
    # Step 4: Create final CSV
    final_df = create_final_csv(enhanced_df)
    
    # Step 5: Update HTML
    update_html_file()
    
    # Step 6: Cleanup
    cleanup_old_files()
    
    # Final summary
    print(f"\n🎉 COLLECTION BUILD COMPLETE!")
    print("=" * 40)
    print(f"✅ Total games: {len(final_df)}")
    print(f"✅ With BGG ranking: {len(final_df[final_df['rank'] != 999999])}")
    print(f"✅ With images: {len(final_df[~final_df['image_filename'].isin(['NO_IMAGE', 'DOWNLOAD_FAILED', ''])])}")
    print(f"✅ With detailed info: {len(final_df[final_df['complexity_weight'] != ''])}")
    
    print(f"\n📁 FILES CREATED:")
    print(f"   📊 brett_spiele_enhanced.csv - Complete collection data")
    print(f"   🖼️  images/ - Game images folder")
    print(f"   🌐 board_games_collection.html - Webpage (if exists)")
    
    print(f"\n🚀 READY TO VIEW:")
    print(f"   Run: python start_server.py")
    print(f"   Visit: http://localhost:8000/board_games_collection.html")
    
    # Show some sample data
    sample_games = final_df[final_df['complexity_weight'] != ''].head(3)
    if not sample_games.empty:
        print(f"\n📊 Sample Enhanced Games:")
        for _, game in sample_games.iterrows():
            print(f"   🎲 {game['name']}")
            print(f"      Players: {game['min_players']}-{game['max_players']} (Best: {game['best_player_count']})")
            print(f"      Time: {game['playing_time']}, Weight: {game['complexity_weight']}/5")

if __name__ == "__main__":
    main()