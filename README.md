# House Judiciary Committee Hearing Analysis Tool

This tool efficiently scrapes House Judiciary Committee hearing transcripts from the official GovInfo website and generates detailed attendance records for legislators using AI analysis. The tool processes all 28 actual Judiciary Committee hearings in the 119th Congress with optimized API usage and smart filtering.

**OPTIMIZED**: Uses the free GovInfo API for hearing discovery and simple text filtering, only calling the expensive Anthropic API for final data extraction from confirmed Judiciary hearings.

## Features:
- **Efficient Discovery**: Uses free GovInfo API with precise search queries to find only actual Judiciary Committee hearings
- **Smart Filtering**: Simple text validation eliminates false positives without expensive AI calls
- **Optimized AI Usage**: Anthropic API only called for final data extraction from confirmed hearings (28 calls vs 50+ previously)
- **Attendance Tracking**: Generates detailed attendance records for specific legislators
- **Batch Processing**: Processes hearings in configurable batches with progress tracking
- **Resumption Support**: Can be interrupted and resumed without losing progress
- **Multiple Output Formats**: Saves data as both JSON and Excel files
- **Flexible Execution**: Run via Makefile, bash scripts, or direct Python commands
- **Cost Effective**: Minimizes expensive API usage through intelligent filtering

## What it extracts:
- Date of the hearing
- Title/subject of the hearing
- URL of the hearing transcript
- Subcommittee information (if applicable)
- Complete list of committee/subcommittee members
- List of legislators present at each hearing
- Individual attendance records with statistics

## Setup

1. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   # or using the Makefile:
   make install
   ```

2. Set up your API key:
   ```bash
   # Create a .env file and add your Anthropic API key
   echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
   
   # Get your API key from: https://console.anthropic.com/
   ```

3. Make bash scripts executable (optional):
   ```bash
   chmod +x judiciary scrape attendance
   ```

## Usage

There are three ways to run this tool:

### Option 1: Using Makefile (Recommended)

**Full Analysis** (comprehensive scrape + attendance record):
```bash
make judiciary LAST_NAME=Kamlager-Dove
```

**Comprehensive Scraping** (ALL hearings - NEW DEFAULT):
```bash
make scrape                      # Process ALL hearings in 119th Congress
make scrape-batch BATCH_SIZE=20  # Custom batch size for processing
```

**Legacy Scraping** (5 hearings only):
```bash
make scrape-legacy              # Process only 5 hearings (old behavior)
```

**Attendance Record Only** (requires existing JSON data):
```bash
make attendance LAST_NAME=Kamlager-Dove
```

**Other Commands**:
```bash
make help     # Show all available commands
make clean    # Remove generated files
```

### Option 2: Using Bash Scripts

```bash
./judiciary Kamlager-Dove    # Full analysis
./scrape                     # Scraping only
./attendance Kamlager-Dove   # Attendance record only
```

### Option 3: Direct Python Execution

**Comprehensive Mode** (NEW DEFAULT):
```bash
python3 scrape_judiciary.py                    # Process ALL hearings
python3 scrape_judiciary.py --batch-size 20    # Custom batch size
```

**Legacy Mode**:
```bash
python3 scrape_judiciary.py --legacy           # Process only 5 hearings
```

**Attendance Analysis**:
```bash
python3 attendance_record.py Kamlager-Dove     # Generate attendance record
```

**Help**:
```bash
python3 scrape_judiciary.py --help             # Show all options
```

## How it works:

### Optimized 3-Step Process:
1. **FREE GovInfo API Discovery**: Uses official API with precise search query to find only actual Judiciary Committee hearings (~28 total)
2. **Simple Text Validation**: Basic string matching eliminates false positives without expensive AI calls
3. **AI Extraction**: Anthropic API called ONLY for confirmed Judiciary hearings to extract structured data

### Previous vs Current Efficiency:
- **Old Method**: 50+ API calls for mixed hearings (many false positives)
- **New Method**: ~28 API calls for only confirmed Judiciary hearings
- **Cost Savings**: ~50% reduction in expensive API usage
- **Accuracy**: Only processes actual House Judiciary Committee hearings

## Performance & Expectations:

- **Discovery Phase**: ~30 seconds using free GovInfo API (vs 20-30 minutes previously)
- **Processing Phase**: ~15 seconds per hearing (includes AI analysis and rate limiting)
- **Total Time**: ~10-15 minutes for all 28 Judiciary hearings (vs several hours previously)
- **API Costs**: Only 28 Anthropic API calls (vs 50+ previously)
- **Resumption**: Can interrupt (Ctrl+C) and resume later without losing progress

## Output Formats

### JSON Output (scrape_judiciary.json)
The scraped hearing data is saved in JSON format:
```json
[
  {
    "hearing_date": "2024-03-15",
    "hearing_title": "Oversight of the Department of Justice",
    "text_url": "https://www.govinfo.gov/content/pkg/CHRG-119hhrg58430/html/CHRG-119hhrg58430.htm",
    "subcommittee_name": null,
    "committee_members": [
      {
        "name": "Sydney Kamlager-Dove",
        "party": "D",
        "state": "CA",
        "role": "Member"
      }
    ],
    "legislators_present": [
      {
        "name": "Sydney Kamlager-Dove", 
        "party": "D",
        "state": "CA",
        "role": "Member"
      }
    ],
    "source_url": "https://www.govinfo.gov/content/pkg/CHRG-119hhrg58430"
  }
]
```

### Excel Output (Attendance Records)
Individual legislator attendance records are saved as Excel files (e.g., `Kamlager-Dove_judiciary_18-09-2025.xlsx`):

| Hearing Date | Hearing Title | URL | Subcommittee | Attendance |
|--------------|---------------|-----|--------------|------------|
| 2024-03-15 | Oversight of the Department of Justice | https://... | | present |
| 2024-03-20 | Immigration Policy Review | https://... | Immigration and Citizenship | absent |

## Requirements

- Python 3.7+
- Anthropic API key (Claude Sonnet 4 access)
- Internet connection for web scraping and API calls
- Dependencies: `anthropic`, `requests`, `beautifulsoup4`, `pandas`, `openpyxl`

## Project Structure

```
house-judiciary/
├── scrape_judiciary.py    # Main scraping script
├── attendance_record.py   # Attendance analysis script
├── judiciary              # Bash script for full analysis
├── scrape                # Bash script for scraping only
├── attendance            # Bash script for attendance only
├── Makefile              # Build automation
├── requirements.txt      # Python dependencies
└──  .env                  # API key configuration (create this)
```

## Examples

**Process ALL hearings and generate attendance record:**
```bash
make judiciary LAST_NAME=Kamlager-Dove
```

**Comprehensive scraping (all 28 Judiciary hearings):**
```bash
make scrape                      # Process ALL hearings (optimized, ~15 minutes)
make scrape-batch BATCH_SIZE=5   # Smaller batches for testing
```

**Quick testing (legacy mode):**
```bash
make scrape-legacy              # Process only 5 hearings for testing
```

**Generate attendance for multiple legislators:**
```bash
make attendance LAST_NAME=Kamlager-Dove
make attendance LAST_NAME=Raskin  
make attendance LAST_NAME=Gaetz
```

**Resumption example:**
```bash
make scrape                     # Start comprehensive processing
# Press Ctrl+C to interrupt
make scrape                     # Resume from where it left off
```
