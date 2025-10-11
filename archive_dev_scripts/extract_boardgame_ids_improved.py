#!/usr/bin/env python3
"""
Board Game ID Extractor - Improved Version

This script processes a list of board games and extracts their BoardGameGeek IDs.
For games with BGG URLs, it extracts the ID directly.
For games without URLs, it searches BoardGameGeek to find the ID.
Results are saved to a CSV file with progress tracking.
"""

import csv
import re
import time
import requests
from xml.etree import ElementTree as ET
from urllib.parse import quote
import sys
import os

def extract_id_from_url(line):
    """Extract board game ID from a BoardGameGeek URL"""
    url_pattern = r'https://boardgamegeek\.com/boardgame/(\d+)'
    match = re.search(url_pattern, line)
    if match:
        return match.group(1)
    return None

def clean_game_name(line):
    """Clean the game name by removing URLs and comments"""
    # Remove URL if present
    line = re.sub(r'https://boardgamegeek\.com/boardgame/\d+/[^\s]*', '', line)
    # Remove comments (everything after #)
    line = re.sub(r'#.*$', '', line)
    # Remove extra whitespace
    line = line.strip()
    return line

def search_boardgamegeek(game_name, max_retries=3, base_delay=2):
    """Search BoardGameGeek for a game and return the best match ID"""
    if not game_name or game_name == "???":
        return None, "Empty or unknown game name"
    
    # BGG XML API search endpoint
    search_url = f"https://boardgamegeek.com/xmlapi2/search?query={quote(game_name)}&type=boardgame"
    
    for attempt in range(max_retries):
        try:
            print(f"  Searching BGG for: '{game_name}' (attempt {attempt + 1})")
            response = requests.get(search_url, timeout=15)
            
            if response.status_code == 429:  # Too Many Requests
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                print(f"    Rate limited, waiting {delay} seconds...")
                time.sleep(delay)
                continue
                
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Find items
            items = root.findall('.//item')
            if not items:
                return None, "No results found"
            
            # Look for exact match first, then best approximation
            best_match = None
            exact_match = None
            
            for item in items:
                item_id = item.get('id')
                names = item.findall('.//name')
                
                for name in names:
                    name_value = name.get('value', '').lower()
                    game_name_lower = game_name.lower()
                    
                    # Check for exact match
                    if name_value == game_name_lower:
                        exact_match = item_id
                        break
                    
                    # Check for close match (contains the search term)
                    if game_name_lower in name_value or name_value in game_name_lower:
                        if best_match is None:
                            best_match = item_id
                
                if exact_match:
                    break
            
            result_id = exact_match or best_match
            if result_id:
                return result_id, "Found"
            else:
                return None, "No good match found"
                
        except requests.exceptions.RequestException as e:
            print(f"    Request failed (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"    Waiting {delay} seconds before retry...")
                time.sleep(delay)
            else:
                return None, f"Request failed after {max_retries} attempts: {str(e)}"
        except ET.ParseError as e:
            return None, f"XML parsing error: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"
    
    return None, "Max retries exceeded"

def load_existing_results(output_file):
    """Load existing results if the file exists"""
    if not os.path.exists(output_file):
        return {}
    
    results = {}
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results[row['original_line']] = row
        print(f"Loaded {len(results)} existing results from {output_file}")
    except Exception as e:
        print(f"Error loading existing results: {str(e)}")
        return {}
    
    return results

def save_results_incremental(results, output_file):
    """Save results incrementally"""
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['original_line', 'game_name', 'bgg_id', 'status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in results.values():
                writer.writerow(result)
    except Exception as e:
        print(f"Error saving results: {str(e)}")

def process_boardgames_list(input_file, output_file):
    """Process the list of board games and extract IDs"""
    print(f"Reading games from: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File {input_file} not found!")
        return
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return
    
    # Load existing results
    existing_results = load_existing_results(output_file)
    results = existing_results.copy()
    
    print(f"Found {len(lines)} lines to process")
    processed_count = len(existing_results)
    print(f"Already processed: {processed_count}")
    print(f"Remaining: {len(lines) - processed_count}\n")
    
    try:
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line == "???":
                continue
            
            # Skip if already processed
            if line in results:
                print(f"Skipping {i}/{len(lines)}: Already processed")
                continue
                
            print(f"Processing {i}/{len(lines)}: {line[:50]}...")
            
            # Try to extract ID from URL first
            game_id = extract_id_from_url(line)
            
            if game_id:
                game_name = clean_game_name(line)
                status = "Extracted from URL"
                print(f"  ✓ Found ID in URL: {game_id}")
            else:
                # No URL found, search BGG
                game_name = clean_game_name(line)
                if game_name:
                    game_id, status = search_boardgamegeek(game_name)
                    if game_id:
                        print(f"  ✓ Found via search: {game_id}")
                    else:
                        print(f"  ✗ Search failed: {status}")
                else:
                    game_id = None
                    status = "Empty game name"
                    print(f"  ✗ Empty game name")
            
            # Add result
            results[line] = {
                'original_line': line,
                'game_name': game_name,
                'bgg_id': game_id,
                'status': status
            }
            
            # Save results every 10 items
            if len(results) % 10 == 0:
                save_results_incremental(results, output_file)
                print(f"  (Saved progress: {len(results)} items)")
            
            # Be nice to BGG servers - add delay between searches
            if not extract_id_from_url(line):
                time.sleep(3)  # Increased delay to avoid rate limiting
            
            print()
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Saving current progress...")
        save_results_incremental(results, output_file)
        print("Progress saved.")
        return
    
    # Write final results to CSV
    print(f"Writing final results to: {output_file}")
    save_results_incremental(results, output_file)
    
    print(f"✓ Results saved successfully!")
    
    # Print summary
    valid_results = [r for r in results.values() if r['original_line'].strip() and r['original_line'] != "???"]
    total_games = len(valid_results)
    found_ids = len([r for r in valid_results if r['bgg_id']])
    print(f"\nSummary:")
    print(f"Total games processed: {total_games}")
    print(f"IDs found: {found_ids}")
    print(f"IDs missing: {total_games - found_ids}")
    if total_games > 0:
        print(f"Success rate: {found_ids/total_games*100:.1f}%")

def main():
    """Main function"""
    input_file = "list.txt"
    output_file = "boardgame_ids.csv"
    
    print("Board Game ID Extractor - Improved Version")
    print("=" * 50)
    
    # Check if requests module is available
    try:
        import requests
    except ImportError:
        print("Error: requests module not found!")
        print("Please install it with: pip install requests")
        return
    
    process_boardgames_list(input_file, output_file)

if __name__ == "__main__":
    main()