#!/usr/bin/env python3
"""
Step 1: Extract BGG IDs from Game List

This script takes list.txt and extracts BoardGameGeek IDs for each game.
It tries multiple methods:
1. Extract from BGG URLs in the list
2. Search BGG API for game names
3. Manual verification for ambiguous results

Output: boardgame_ids.csv (ready for manual editing if needed)
"""

import pandas as pd
import requests
import xml.etree.ElementTree as ET
import time
import re
import sys
from datetime import datetime

def extract_id_from_url(line):
    """Extract BGG ID from URLs in the line"""
    # Look for BGG URLs with game IDs
    patterns = [
        r'boardgamegeek\.com/boardgame/(\d+)',
        r'bgg\.cc/(\d+)',
        r'/(\d+)/'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            return int(match.group(1))
    return None

def clean_game_name(name):
    """Clean game name for better API searching"""
    # Remove common prefixes and suffixes
    name = re.sub(r'^\d+\.\s*', '', name)  # Remove numbering
    name = re.sub(r'\s*#.*$', '', name)    # Remove comments
    name = re.sub(r'\s*\(.*\)$', '', name) # Remove parentheses
    name = re.sub(r'\s*–.*$', '', name)    # Remove em-dash and after
    name = re.sub(r'\s*-.*expansion.*$', '', name, flags=re.IGNORECASE)
    name = name.strip()
    return name

def search_bgg_for_game(game_name, max_results=5):
    """Search BGG API for a game by name"""
    if not game_name:
        return []
    
    try:
        # Use BGG search API
        search_url = "https://boardgamegeek.com/xmlapi2/search"
        params = {
            'query': game_name,
            'type': 'boardgame'
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        results = []
        
        for item in root.findall('.//item')[:max_results]:
            bgg_id = item.get('id')
            name = item.find('.//name')
            year = item.find('.//yearpublished')
            
            if name is not None and bgg_id:
                result = {
                    'id': int(bgg_id),
                    'name': name.get('value', ''),
                    'year': year.get('value', '') if year is not None else ''
                }
                results.append(result)
        
        return results
        
    except Exception as e:
        print(f"❌ Error searching for '{game_name}': {e}")
        return []

def get_exact_game_info(bgg_id):
    """Get exact game information from BGG API"""
    try:
        url = f"https://boardgamegeek.com/xmlapi2/thing?id={bgg_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        item = root.find('.//item')
        
        if item is None:
            return None
        
        primary_name = item.find('.//name[@type="primary"]')
        year = item.find('.//yearpublished')
        
        return {
            'id': int(bgg_id),
            'name': primary_name.get('value') if primary_name is not None else '',
            'year': year.get('value') if year is not None else ''
        }
        
    except Exception as e:
        print(f"❌ Error getting info for ID {bgg_id}: {e}")
        return None

def find_best_match(original_name, search_results):
    """Find the best match from search results"""
    if not search_results:
        return None
    
    original_lower = original_name.lower()
    
    # Exact match first
    for result in search_results:
        if result['name'].lower() == original_lower:
            return result
    
    # Partial match
    for result in search_results:
        if original_lower in result['name'].lower() or result['name'].lower() in original_lower:
            return result
    
    # Return first result if no good match
    return search_results[0]

def extract_bgg_ids():
    """Main function to extract BGG IDs from list.txt"""
    
    print("🎲 BGG ID Extraction - Step 1")
    print("=" * 40)
    
    # Read the game list
    try:
        with open('list.txt', 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        print(f"✓ Loaded {len(lines)} games from list.txt")
    except FileNotFoundError:
        print("❌ list.txt not found!")
        return
    
    results = []
    total_games = len(lines)
    
    print(f"\n🚀 Processing {total_games} games...")
    print("⏱️  This will take several minutes due to API rate limiting")
    
    for i, line in enumerate(lines, 1):
        print(f"\n[{i}/{total_games}] 🎯 Processing: {line[:50]}...")
        
        result = {
            'original_line': line,
            'game_name': '',
            'bgg_id': '',
            'matched_name': '',
            'year': '',
            'status': '',
            'confidence': ''
        }
        
        # Try to extract ID from URL first
        url_id = extract_id_from_url(line)
        if url_id:
            print(f"   ✓ Found ID from URL: {url_id}")
            game_info = get_exact_game_info(url_id)
            if game_info:
                result.update({
                    'game_name': clean_game_name(line.split('/')[-1]) or game_info['name'],
                    'bgg_id': game_info['id'],
                    'matched_name': game_info['name'],
                    'year': game_info['year'],
                    'status': 'Found from URL',
                    'confidence': 'High'
                })
            else:
                result.update({
                    'game_name': clean_game_name(line),
                    'status': 'Invalid URL ID',
                    'confidence': 'None'
                })
        else:
            # Extract game name and search BGG
            game_name = clean_game_name(line)
            result['game_name'] = game_name
            
            if game_name:
                print(f"   🔍 Searching BGG for: '{game_name}'")
                search_results = search_bgg_for_game(game_name)
                
                if search_results:
                    best_match = find_best_match(game_name, search_results)
                    if best_match:
                        # Determine confidence level
                        if best_match['name'].lower() == game_name.lower():
                            confidence = 'High'
                        elif game_name.lower() in best_match['name'].lower():
                            confidence = 'Medium'
                        else:
                            confidence = 'Low'
                        
                        result.update({
                            'bgg_id': best_match['id'],
                            'matched_name': best_match['name'],
                            'year': best_match['year'],
                            'status': 'Found via search',
                            'confidence': confidence
                        })
                        
                        print(f"   ✓ Found: {best_match['name']} ({best_match['year']}) - ID: {best_match['id']} [{confidence}]")
                        
                        # Show alternatives if confidence is low
                        if confidence == 'Low' and len(search_results) > 1:
                            print("   📋 Other options found:")
                            for j, alt in enumerate(search_results[1:4], 2):
                                print(f"      {j}. {alt['name']} ({alt['year']}) - ID: {alt['id']}")
                    else:
                        result.update({
                            'status': 'No good match',
                            'confidence': 'None'
                        })
                        print("   ❌ No good match found")
                else:
                    result.update({
                        'status': 'Not found',
                        'confidence': 'None'
                    })
                    print("   ❌ No results from BGG search")
            else:
                result.update({
                    'status': 'Invalid name',
                    'confidence': 'None'
                })
                print("   ❌ Could not extract game name")
        
        results.append(result)
        
        # Rate limiting
        print("   ⏳ Waiting 2 seconds...")
        time.sleep(2)
        
        # Save progress every 10 games
        if i % 10 == 0:
            backup_filename = f'boardgame_ids_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            df_backup = pd.DataFrame(results)
            df_backup.to_csv(backup_filename, index=False)
            print(f"   💾 Progress saved to {backup_filename}")
    
    # Save final results
    df = pd.DataFrame(results)
    df.to_csv('boardgame_ids.csv', index=False)
    
    # Generate summary
    found_count = len(df[df['bgg_id'] != ''])
    high_conf = len(df[df['confidence'] == 'High'])
    medium_conf = len(df[df['confidence'] == 'Medium'])
    low_conf = len(df[df['confidence'] == 'Low'])
    not_found = len(df[df['bgg_id'] == ''])
    
    print(f"\n🎉 EXTRACTION COMPLETE!")
    print("=" * 30)
    print(f"✅ Total games processed: {total_games}")
    print(f"✅ BGG IDs found: {found_count} ({found_count/total_games*100:.1f}%)")
    print(f"   🟢 High confidence: {high_conf}")
    print(f"   🟡 Medium confidence: {medium_conf}")
    print(f"   🟠 Low confidence: {low_conf}")
    print(f"❌ Not found: {not_found}")
    print(f"\n💾 Results saved to: boardgame_ids.csv")
    
    if low_conf > 0 or not_found > 0:
        print(f"\n📝 MANUAL REVIEW RECOMMENDED:")
        print(f"   - Check {low_conf} low-confidence matches")
        print(f"   - Research {not_found} games not found")
        print(f"   - Edit boardgame_ids.csv as needed")
        print(f"   - You can add BGG IDs manually in the 'bgg_id' column")
    
    print(f"\n➡️  Next step: Run step2_build_collection.py")

if __name__ == "__main__":
    extract_bgg_ids()