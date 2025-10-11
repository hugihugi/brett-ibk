# Board Game Collection Builder

A streamlined two-step process to create a comprehensive board game collection from a simple text list.

## 🎯 Overview

Transform your board game list into a professional web-based collection with:
- BGG rankings and ratings
- Game images from BoardGameGeek
- Detailed information (player counts, complexity, playing time)
- Interactive web interface with search and filters

## 📋 Prerequisites

1. **Python 3.7+** with packages: `pandas`, `requests`
2. **list.txt** - Your game list (one game per line)
3. **boardgames_ranks.csv** (optional) - BGG ranking data for enhanced info

## 🚀 Quick Start

### Step 1: Extract BGG IDs
```bash
python step1_extract_ids.py
```
- Reads `list.txt`
- Extracts BGG IDs from URLs or searches BGG API
- Creates `boardgame_ids.csv`
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
├── 📄 list.txt                      # Input: Your game list
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
- Create `list.txt` with one game per line
- Games can be names or BGG URLs

**"Low success rate in Step 1"**
- Use BGG URLs when possible: `https://boardgamegeek.com/boardgame/12345/game-name`
- Clean up game names (remove expansions, versions)
- Manually edit `boardgame_ids.csv`

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
- **With BGG URLs**: ~95-100%
- **With clean game names**: ~80-90%
- **With messy names**: ~60-70%

## 🏆 Final Result

A professional board game collection website featuring:
- Interactive browsing with images
- Comprehensive BGG data integration
- Mobile and desktop friendly
- Easy sharing and hosting options

## 🔄 Updates

To update your collection:
1. Add new games to `list.txt`
2. Re-run both steps
3. Or manually add to `boardgame_ids.csv` and run step 2

---

**Enjoy your enhanced board game collection! 🎲**