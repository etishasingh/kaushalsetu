# KaushalSetu AI — YouTube Career Journey Recommendation Engine

This folder is a **self-contained, standalone deliverable** containing everything needed to run, explore, test, and integrate authentic vocational YouTube career journey videos into KaushalSetu AI.

---

## 1. Deliverable Contents

| File | Purpose | Execution Method |
|---|---|---|
| [`youtube_recommendation.py`](./youtube_recommendation.py) | Standalone Python Recommendation Engine & CLI | `python youtube_recommendation.py` |
| [`career_videos_cache.json`](./career_videos_cache.json) | Persistent structured JSON cache with 7 verified trades | Auto-loaded by Python engine & web tools |
| [`run_youtube_recommendation.bat`](./run_youtube_recommendation.bat) | Windows Executable Batch Launcher | **Double-click** in Windows Explorer |
| [`youtube_career_videos.html`](./youtube_career_videos.html) | Standalone Executable Interactive Web Explorer | **Double-click** to open in any web browser |
| [`README.md`](./README.md) | Package documentation & API integration guide | Markdown viewer |

---

## 2. Key Features

- **Zero External Dependencies:** Built entirely with Python's standard library (`urllib`, `json`, `argparse`, `re`, `datetime`). It works immediately on any standard Python 3.8+ installation without running `pip install`.
- **Pre-Cached Authentic Videos:** Includes verified authentic career journey videos for:
  1. **Stainless Steel Fabricator** (2022/CCM/CGSC/06612)
  2. **Welder (SMAW / GMAW)** (QG-02-CG-03939-2025-V2-CGSSC)
  3. **CNC Milling & Turning Operator** (cnc)
  4. **Mechanical Fitter & Assembler** (QG-3.5-CG-01029-2023-V1-NTTF)
  5. **Industrial Electrician & Wireman** (electrician)
  6. **Sheet Metal Worker** (QG-04-CG-03209-2024-V2-DGT)
  7. **Instrumentation Technician (Process Control)** (2022/ETR/IASC/06501)
- **4-Category Taxonomy:**
  - `start_here`: Basics & Getting Started
  - `real_journey`: Real Career Journeys — How Professionals Started
  - `skills_training`: Skills & Practical Training
  - `career_growth`: Career Growth & Work Experience
- **Quality & Anti-Clickbait Scoring:** Transparent [0.0 - 1.0] scoring filtering out commercial spam, gaming, or entertainment videos while prioritizing authentic shop-floor realities and ITI training.
- **Official Demarcation:** Clearly demarcates personal practitioner videos from official NCVET qualification register criteria.

---

## 3. How to Run

### Method 1: Double-Click Executable Batch (Windows)
Double-click `run_youtube_recommendation.bat` in Windows Explorer:
- Opens an interactive terminal console.
- Displays all available cached trades.
- Lets you select a trade, choose English or Hindi, and see results instantly with ASCII relevance match bars.

### Method 2: Double-Click Interactive Web Explorer
Double-click `youtube_career_videos.html` in your file browser:
- Opens instantly in Google Chrome, Microsoft Edge, Firefox, or Safari.
- Lets you search by trade title or skill.
- Lets you filter by trade chips or category tabs.
- Watch videos directly on YouTube with one click.

### Method 3: Command Line Usage (CLI)

```bash
# Interactive menu:
python youtube_recommendation.py

# Query by trade title:
python youtube_recommendation.py --career "Welder"

# Query by qualification ID and language:
python youtube_recommendation.py --career-id "2022/CCM/CGSC/06612" --language "Hindi"

# Filter by category:
python youtube_recommendation.py --career "CNC Operator" --category "real_journey"

# Output clean JSON to stdout (for piping into other scripts/tools):
python youtube_recommendation.py --career "Fabricator" --json

# Export recommendation results to a JSON file:
python youtube_recommendation.py --career "Electrician" --export "electrician_results.json"

# List all available pre-cached trades:
python youtube_recommendation.py --list
```

---

## 4. How to Import in Python Projects

You can drop `youtube_recommendation.py` directly into any Python project:

```python
from youtube_recommendation import YouTubeRecommendationEngine

# Get singleton engine instance
engine = YouTubeRecommendationEngine.get_instance()

# Query career videos
result = engine.get_career_videos(
    career_id="2022/CCM/CGSC/06612",
    career_title="Stainless Steel Fabricator",
    language="English"
)

print(f"Total videos: {result.total_videos}")
for category_key, videos in result.categories.items():
    print(f"\nCategory: {category_key} ({len(videos)} videos)")
    for v in videos:
        print(f" - {v.video_title} ({v.video_url}) [Score: {v.relevance_score}]")
```

---

## 5. Live YouTube Data API v3 Configuration (Optional)

By default, the engine uses verified cached data and requires zero internet connection or API keys.

If you wish to discover new live videos from YouTube:
1. Obtain an official YouTube Data API v3 key from Google Cloud Console.
2. Set the environment variable:
   ```bash
   # Windows PowerShell
   $env:YOUTUBE_API_KEY="your-api-key-here"

   # Windows Command Prompt
   set YOUTUBE_API_KEY=your-api-key-here
   ```
3. Run with `--force-refresh`:
   ```bash
   python youtube_recommendation.py --career "Solar Panel Technician" --force-refresh
   ```
The engine will query YouTube Data API v3, filter out clickbait, score relevance, organize the videos into the 4 categories, and automatically update `career_videos_cache.json` for future offline use.
