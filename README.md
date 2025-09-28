# House Judiciary Committee Hearing Analysis Tool

This tool scrapes House Judiciary Committee hearing transcripts from the GovInfo website and generates detailed attendance records for legislators using AI analysis. The tool can process **ALL hearings** in the 119th Congress with comprehensive search capabilities and resumption support.

**NEW**: Comprehensive mode finds and processes every hearing in the 119th Congress with batch processing and resumption capabilities. 

## Features:
- **🔍 Comprehensive Search**: Systematically finds ALL hearings in the 119th Congress using sequential search
- **🤖 AI Analysis**: Uses Claude Sonnet 4 to extract structured information from transcripts
- **📊 Attendance Tracking**: Generates detailed attendance records for specific legislators
- **📦 Batch Processing**: Processes hearings in configurable batches with progress tracking
- **💾 Resumption Support**: Can be interrupted and resumed without losing progress
- **📄 Multiple Output Formats**: Saves data as both JSON and Excel files
- **⚙️ Flexible Execution**: Run via Makefile, bash scripts, or direct Python commands
- **🎛️ Multiple Modes**: Choose between comprehensive (all hearings) or legacy (5 hearings) modes

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
make judiciary LAST_NAME=Jordan
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
make attendance LAST_NAME=Jordan
```

**Other Commands**:
```bash
make help     # Show all available commands
make clean    # Remove generated files
```

### Option 2: Using Bash Scripts

```bash
./judiciary Jordan    # Full analysis
./scrape             # Scraping only
./attendance Jordan  # Attendance record only
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
python3 attendance_record.py Jordan            # Generate attendance record
```

**Help**:
```bash
python3 scrape_judiciary.py --help             # Show all options
```

## How it works:

### Comprehensive Mode (Default):
1. **🔍 Discovery Phase**: Systematically searches hearing numbers (50000+) until 200 consecutive failures
2. **📦 Batch Processing**: Processes found hearings in configurable batches (default: 10)
3. **🤖 AI Analysis**: Each transcript is analyzed by Claude Sonnet 4 to extract structured information
4. **💾 Progress Saving**: Results saved after each hearing for resumption capability
5. **📊 Attendance Analysis**: Generates Excel reports for specific legislators

### Legacy Mode:
1. **Limited Search**: Tests every 50th number in range 50000-70000
2. **Quick Processing**: Processes first 5 hearings found
3. **Single Batch**: All processing in one session

## Performance & Expectations:

- **Discovery Phase**: ~20-30 minutes to find all hearings (0.1s delays between requests)
- **Processing Phase**: ~3-5 seconds per hearing (includes API calls and rate limiting)
- **Resumption**: Can interrupt (Ctrl+C) and resume later without losing progress
- **Total Time**: Several hours for complete 119th Congress analysis
- **API Costs**: Proportional to number of hearings processed (Claude Sonnet 4 usage)

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
        "name": "Jim Jordan",
        "party": "R",
        "state": "OH",
        "role": "Chairman"
      }
    ],
    "legislators_present": [
      {
        "name": "Jim Jordan", 
        "party": "R",
        "state": "OH",
        "role": "Chairman"
      }
    ],
    "source_url": "https://www.govinfo.gov/content/pkg/CHRG-119hhrg58430"
  }
]
```

### Excel Output (Attendance Records)
Individual legislator attendance records are saved as Excel files (e.g., `Jordan_judiciary_18-09-2025.xlsx`):

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
make judiciary LAST_NAME=Jordan
```

**Comprehensive scraping (all hearings):**
```bash
make scrape                      # Process ALL hearings (may take hours)
make scrape-batch BATCH_SIZE=5   # Smaller batches for testing
```

**Quick testing (legacy mode):**
```bash
make scrape-legacy              # Process only 5 hearings for testing
```

**Generate attendance for multiple legislators:**
```bash
make attendance LAST_NAME=Jordan
make attendance LAST_NAME=Raskin  
make attendance LAST_NAME=Gaetz
```

**Resumption example:**
```bash
make scrape                     # Start comprehensive processing
# Press Ctrl+C to interrupt
make scrape                     # Resume from where it left off
```
