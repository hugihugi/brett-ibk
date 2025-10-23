# Brett Innsbruck - Board Game Collection

A streamlined two-step process to create a comprehensive board game collection from a simple text list.

## 🎯 Overview

Transform your board game list into a professional web-based collection with:
- BGG rankings and ratings
- Game images from BoardGameGeek
- Detailed information (player counts, complexity, playing time)
- Interactive web interface with search and filters

## 📋 Prerequisites

1. **Python 3.7+** with packages: `pandas`, `requests`
2. **list2.txt** (or **list.txt**) - Your game list (one game per line)
   - Format: `https://boardgamegeek.com/boardgame/ID/slug # Custom Name`
   - The custom name after `#` will be displayed instead of the BGG name
3. **boardgames_ranks.csv** (optional) - BGG ranking data for enhanced info

## 🚀 Quick Start

### Step 1: Extract BGG IDs
```bash
python step1_extract_ids.py
```
- Reads `list2.txt` (or falls back to `list.txt`)
- Extracts BGG IDs from URLs (preferred format)
- Captures custom game names from comments (after `#`)
- Creates `boardgame_ids.csv` with columns: `custom_name`, `bgg_link`, `bgg_id`
- **Manual review recommended** for low-confidence matches

### Step 2: Build Collection
```bash
python step2_build_collection.py
```
- Uses `boardgame_ids.csv` from step 1
- Downloads game images
- Fetches detailed BGG information
- Creates complete collection website

### Step 3: View Collection
```bash
python start_server.py
```
- Visit: http://localhost:8000/board_games_collection.html

## 📁 File Structure

```
📂 Your Folder
├── 📄 list2.txt                     # Input: Your game list (with BGG links & custom names)
├── 📄 list.txt                      # Old format (fallback)
├── 📄 boardgames_ranks.csv         # Optional: BGG ranking data
│
├── 🔧 step1_extract_ids.py         # Step 1: Extract BGG IDs
├── 🔧 step2_build_collection.py    # Step 2: Build collection
├── 🔧 start_server.py              # Web server
│
├── 📊 boardgame_ids.csv            # Output from Step 1
├── 📊 brett_spiele_enhanced.csv    # Final collection data
├── 🌐 board_games_collection.html  # Collection webpage
└── 📁 images/                      # Game images
```

## 🔧 Manual Review (Step 1.5)

After step 1, review `boardgame_ids.csv`:
- Check games with `confidence: Low`
- Add missing BGG IDs manually
- Fix incorrect matches

**CSV Columns:**
- `custom_name`: Your custom name for the game (from `#` comments)
- `bgg_link`: Direct link to BGG page
- `bgg_id`: Add or correct BGG IDs here
- `confidence`: High/Medium/Low/None
- `status`: Found/Not found/Manual review needed

## ⚙️ Advanced Options

### Custom Port
```bash
python start_server.py --port 8001
```

### Force Refresh
Delete these files to regenerate:
- `boardgame_ids.csv` - Re-extract BGG IDs
- `brett_spiele_enhanced.csv` - Re-build collection
- `images/` folder - Re-download images

## 🎮 Features

### Collection Website
- **Grid/List views** with game images
- **Custom game names** - displays your names from list2.txt
- **BGG links** - direct links to BoardGameGeek in game modals
- **Search** by game name
- **Filters**: Type, rating, player count, complexity
- **Sort**: Rank, rating, name, year, complexity, players
- **Mobile responsive** design

### Game Information
- **BGG Rank & Rating**
- **Player Count** (min-max + community best)
- **Playing Time** from BGG
- **Complexity Weight** (1-5 scale)
- **Game Mechanics & Categories**
- **High-quality images**

## 🔧 Troubleshooting

### Common Issues

**"list.txt not found"**
- Create `list2.txt` with one game per line
- **Recommended format**: `https://boardgamegeek.com/boardgame/ID/slug # Custom Name`
- Example: `https://boardgamegeek.com/boardgame/322708/descent-legends-of-the-dark # Descent`
- The custom name after `#` will be displayed on your website

**"Low success rate in Step 1"**
- **Always use direct BGG links** for 100% accuracy
- Format: `https://boardgamegeek.com/boardgame/12345/game-name # Your Custom Name`
- Manually edit `boardgame_ids.csv` if needed

**"Images not downloading"**
- Check internet connection
- BGG API rate limiting (script waits 2 seconds between requests)
- Some games may not have images

**"Port already in use"**
- Try different port: `python start_server.py --port 8001`
- Or stop other servers

### Manual Fixes

**Add BGG ID manually:**
1. Find game on BoardGameGeek
2. Copy ID from URL: `boardgamegeek.com/boardgame/ID/name`
3. Add to `bgg_id` column in `boardgame_ids.csv`
4. Re-run step 2

**Fix incorrect match:**
1. Edit `bgg_id` in `boardgame_ids.csv`
2. Re-run step 2

## 📈 Success Rates

Typical success rates:
- **With direct BGG links (list2.txt format)**: 100% ✅
- **With BGG URLs (old format)**: ~95-100%
- **With clean game names**: ~80-90%
- **With messy names**: ~60-70%

**💡 Tip**: Always use the new `list2.txt` format with direct links and custom names!

## 🏆 Final Result

A professional board game collection website featuring:
- Interactive browsing with images
- Comprehensive BGG data integration
- Mobile and desktop friendly
- Easy sharing and hosting options

## 🔄 Updates

To update your collection:
1. Add new games to `list2.txt` (format: `BGG_LINK # Custom Name`)
2. Re-run both steps
3. Or manually add to `boardgame_ids.csv` and run step 2

## 🆕 New Features (list2.txt)

- **Custom game names**: Use your own names instead of BGG database names
- **Direct BGG links**: Each game card has a button to view on BoardGameGeek
- **100% accuracy**: Direct links eliminate search ambiguity
- **Multilingual support**: Use names in your own language

**Example list2.txt entry:**
```
https://boardgamegeek.com/boardgame/322708/descent-legends-of-the-dark # Descent
https://boardgamegeek.com/boardgame/193037/dead-of-winter-the-long-night # Winter der Toten - Lange Nacht
```

---

**Enjoy your enhanced board game collection! 🎲**
