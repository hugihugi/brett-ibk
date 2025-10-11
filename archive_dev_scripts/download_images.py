#!/usr/bin/env python3
"""
Board Game Image Downloader

This script downloads board game images from BoardGameGeek using the BGG XML API
and saves them to a local folder, then adds the image filenames to the CSV.
"""

import pandas as pd
import requests
import os
import time
import re
from xml.etree import ElementTree as ET
from urllib.parse import urlparse
import unicodedata

def sanitize_filename(filename):
    """Sanitize filename for Windows/cross-platform compatibility"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove control characters
    filename = ''.join(c for c in filename if ord(c) >= 32)
    # Normalize unicode
    filename = unicodedata.normalize('NFKD', filename)
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    return filename.strip()

def get_game_info_and_image(bgg_id, max_retries=3):
    """Get game information and image URL from BGG API"""
    api_url = f"https://boardgamegeek.com/xmlapi2/thing?id={bgg_id}&stats=1"
    
    for attempt in range(max_retries):
        try:
            print(f"    Fetching BGG data (attempt {attempt + 1})...")
            response = requests.get(api_url, timeout=15)
            
            if response.status_code == 429:  # Too Many Requests
                delay = 2 ** attempt
                print(f"    Rate limited, waiting {delay} seconds...")
                time.sleep(delay)
                continue
            
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            item = root.find('.//item')
            
            if item is None:
                return None, None, "No game data found"
            
            # Get image URL
            image_elem = item.find('image')
            image_url = image_elem.text if image_elem is not None else None
            
            # Get game name for filename
            name_elem = item.find('.//name[@type="primary"]')
            if name_elem is None:
                name_elem = item.find('.//name')
            game_name = name_elem.get('value') if name_elem is not None else f"game_{bgg_id}"
            
            # Get year for filename
            year_elem = item.find('yearpublished')
            year = year_elem.get('value') if year_elem is not None else ""
            
            return image_url, game_name, year
            
        except requests.exceptions.RequestException as e:
            print(f"    Request failed (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                delay = 2 ** attempt
                time.sleep(delay)
            else:
                return None, None, f"Request failed after {max_retries} attempts"
        except ET.ParseError as e:
            return None, None, f"XML parsing error: {str(e)}"
        except Exception as e:
            return None, None, f"Unexpected error: {str(e)}"
    
    return None, None, "Max retries exceeded"

def download_image(image_url, filename, images_folder):
    """Download image from URL and save to folder"""
    try:
        print(f"    Downloading image...")
        response = requests.get(image_url, timeout=30, stream=True)
        response.raise_for_status()
        
        # Create full path
        filepath = os.path.join(images_folder, filename)
        
        # Write image data
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Verify file was created and has content
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return True, None
        else:
            return False, "File was not created or is empty"
            
    except requests.exceptions.RequestException as e:
        return False, f"Download failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def process_game_images(csv_file, images_folder="images", skip_existing=True):
    """Process board game images for all games in CSV"""
    
    print("Board Game Image Downloader")
    print("=" * 60)
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_file)
        print(f"✓ Loaded {len(df)} games from {csv_file}")
    except Exception as e:
        print(f"Error reading {csv_file}: {str(e)}")
        return
    
    # Create images folder if it doesn't exist
    if not os.path.exists(images_folder):
        os.makedirs(images_folder)
        print(f"✓ Created images folder: {images_folder}")
    else:
        print(f"✓ Using existing images folder: {images_folder}")
    
    # Add image filename column if it doesn't exist
    if 'image_filename' not in df.columns:
        df['image_filename'] = ''
    
    # Process each game
    successful_downloads = 0
    skipped_games = 0
    failed_downloads = 0
    
    for index, row in df.iterrows():
        bgg_id = row['bgg_id']
        game_name = row['name'] if pd.notna(row['name']) else row['game_name']
        
        print(f"\nProcessing {index + 1}/{len(df)}: {game_name}")
        
        # Skip if no BGG ID
        if pd.isna(bgg_id) or bgg_id == '':
            print(f"  ⏭️  Skipping - No BGG ID")
            df.at[index, 'image_filename'] = 'NO_BGG_ID'
            skipped_games += 1
            continue
        
        # Convert BGG ID to integer
        try:
            bgg_id = int(float(bgg_id))
        except (ValueError, TypeError):
            print(f"  ⏭️  Skipping - Invalid BGG ID: {bgg_id}")
            df.at[index, 'image_filename'] = 'INVALID_ID'
            skipped_games += 1
            continue
        
        # Check if image already exists
        if skip_existing and pd.notna(row['image_filename']) and row['image_filename'] not in ['', 'NO_BGG_ID', 'INVALID_ID', 'DOWNLOAD_FAILED', 'NO_IMAGE']:
            existing_path = os.path.join(images_folder, row['image_filename'])
            if os.path.exists(existing_path):
                print(f"  ✓ Already exists: {row['image_filename']}")
                skipped_games += 1
                continue
        
        # Get game info and image URL
        image_url, api_game_name, year = get_game_info_and_image(bgg_id)
        
        if not image_url:
            print(f"  ❌ No image URL found")
            df.at[index, 'image_filename'] = 'NO_IMAGE'
            failed_downloads += 1
            time.sleep(1)  # Be nice to BGG servers
            continue
        
        # Create filename
        display_name = api_game_name if api_game_name else game_name
        year_suffix = f"_{year}" if year else ""
        
        # Get file extension from URL
        parsed_url = urlparse(image_url)
        file_ext = os.path.splitext(parsed_url.path)[1]
        if not file_ext:
            file_ext = '.jpg'  # Default extension
        
        # Create sanitized filename
        base_name = f"{display_name}{year_suffix}_{bgg_id}"
        filename = sanitize_filename(base_name) + file_ext
        
        print(f"  📁 Filename: {filename}")
        
        # Download image
        success, error = download_image(image_url, filename, images_folder)
        
        if success:
            print(f"  ✅ Downloaded successfully")
            df.at[index, 'image_filename'] = filename
            successful_downloads += 1
        else:
            print(f"  ❌ Download failed: {error}")
            df.at[index, 'image_filename'] = 'DOWNLOAD_FAILED'
            failed_downloads += 1
        
        # Save progress every 10 games
        if (index + 1) % 10 == 0:
            df.to_csv(csv_file, index=False, encoding='utf-8')
            print(f"  💾 Progress saved ({index + 1}/{len(df)})")
        
        # Be nice to BGG servers
        time.sleep(2)
    
    # Save final results
    df.to_csv(csv_file, index=False, encoding='utf-8')
    
    print(f"\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"Total games processed: {len(df)}")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Skipped games: {skipped_games}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Images saved to: {os.path.abspath(images_folder)}")
    print(f"CSV updated: {csv_file}")
    
    # Show some statistics
    existing_images = len([f for f in os.listdir(images_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))])
    print(f"Total images in folder: {existing_images}")
    
    print(f"\n✅ Image download process complete!")

def main():
    """Main function"""
    csv_file = "brett_spiele.csv"
    images_folder = "images"
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        return
    
    try:
        import pandas as pd
        import requests
    except ImportError as e:
        print(f"Error: Required module not found: {e}")
        print("Please install required packages with: pip install pandas requests")
        return
    
    print("This script will download board game images from BoardGameGeek.")
    print("This may take a while depending on your collection size.")
    print("The script will be respectful to BGG servers with delays between requests.")
    
    response = input("\nDo you want to continue? (y/n): ").lower().strip()
    if response != 'y':
        print("Cancelled.")
        return
    
    process_game_images(csv_file, images_folder)

if __name__ == "__main__":
    main()