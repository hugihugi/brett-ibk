#!/usr/bin/env python3
"""
Cleanup Board Game Collection Workspace

This script helps organize your board game collection files by:
- Moving development scripts to an 'archive' folder
- Deleting intermediate data files
- Keeping only essential files for the working website
"""

import os
import shutil
from pathlib import Path

def cleanup_workspace():
    """Clean up the workspace, keeping only essential files"""
    
    print("🧹 Board Game Collection Workspace Cleanup")
    print("=" * 50)
    
    # Files to keep in main directory (essential for website)
    essential_files = {
        'board_games_collection.html',  # Main webpage
        'brett_spiele.csv',      # Data file
        'serve_collection.py',          # Web server
        'list.txt',                     # Original game list (backup)
        'images',                       # Images folder
    }
    
    # Development scripts to archive
    dev_scripts = {
        'extract_boardgame_ids_improved.py',
        'merge_boardgames.py', 
        'download_images.py',
        'analyze_collection.py',
        'cleanup_workspace.py'  # This script itself
    }
    
    # Intermediate files to delete
    intermediate_files = {
        'boardgame_ids.csv',
        'merged_boardgames.csv',
        'boardgames_ranks.csv'  # Large source file no longer needed
    }
    
    # Personal files (user decides)
    personal_files = {
        'brett_ibk.xlsx',
        'foto1.jpeg',
        'foto2.jpeg', 
        'foto3.jpeg',
        'WhatsApp Image 2025-10-09 at 16.47.20.jpeg'
    }
    
    # Create archive folder for development scripts
    archive_dir = 'archive_dev_scripts'
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        print(f"📁 Created '{archive_dir}' folder")
    
    # Move development scripts to archive
    print("\n📦 Archiving development scripts...")
    for script in dev_scripts:
        if os.path.exists(script):
            try:
                shutil.move(script, os.path.join(archive_dir, script))
                print(f"✓ Moved {script} to archive")
            except Exception as e:
                print(f"❌ Error moving {script}: {e}")
    
    # Delete intermediate files
    print("\n🗑️  Deleting intermediate files...")
    for file in intermediate_files:
        if os.path.exists(file):
            try:
                file_size = os.path.getsize(file) / (1024*1024)  # Size in MB
                os.remove(file)
                print(f"✓ Deleted {file} ({file_size:.1f} MB)")
            except Exception as e:
                print(f"❌ Error deleting {file}: {e}")
    
    # Report on personal files
    print("\n👤 Personal files found (you decide what to do):")
    personal_found = []
    for file in personal_files:
        if os.path.exists(file):
            file_size = os.path.getsize(file) / (1024*1024) if os.path.isfile(file) else 0
            personal_found.append(f"   📄 {file} ({file_size:.2f} MB)")
    
    if personal_found:
        for item in personal_found:
            print(item)
        print("   💡 These appear to be personal files - keep or delete as you wish")
    else:
        print("   ✓ No personal files found")
    
    # Summary of what remains
    print("\n📋 FINAL WORKSPACE SUMMARY:")
    print("=" * 30)
    
    current_files = []
    for item in os.listdir('.'):
        if os.path.isfile(item):
            size = os.path.getsize(item) / 1024  # Size in KB
            current_files.append((item, size, 'file'))
        elif os.path.isdir(item):
            current_files.append((item, 0, 'folder'))
    
    # Sort by type then name
    current_files.sort(key=lambda x: (x[2], x[0]))
    
    print("📁 FOLDERS:")
    for name, size, ftype in current_files:
        if ftype == 'folder':
            if name == 'images':
                img_count = len([f for f in os.listdir(name) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
                print(f"   📁 {name}/ ({img_count} images)")
            else:
                print(f"   📁 {name}/")
    
    print("\n📄 FILES:")
    for name, size, ftype in current_files:
        if ftype == 'file':
            if name in essential_files:
                print(f"   ✅ {name} ({size:.1f} KB) - ESSENTIAL")
            elif name in personal_files:
                print(f"   👤 {name} ({size:.1f} KB) - PERSONAL")
            else:
                print(f"   📄 {name} ({size:.1f} KB)")
    
    print("\n🎯 READY TO USE:")
    print("   Your board game collection is clean and ready!")
    print("   Run: python serve_collection.py")
    print("   Then visit: http://localhost:8000/board_games_collection.html")
    
    print(f"\n📚 Development files archived in: {archive_dir}/")
    print("   (You can delete this folder if you don't need the scripts anymore)")

if __name__ == "__main__":
    cleanup_workspace()