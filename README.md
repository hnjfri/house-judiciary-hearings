# House Judiciary Committee Hearing Analysis Tool

This tool scrapes House Judiciary Committee hearing transcripts from the GovInfo website and generates detailed attendance records for legislators using AI analysis.

NOTE: This currently focuses on the 119th Congress, hearing URL search ranges will need to be updated to reflect other sessions. 

## Features:
- **Web Scraping**: Automatically finds and scrapes hearing transcripts from govinfo.gov
- **AI Analysis**: Uses Claude Sonnet 4 to extract structured information from transcripts
- **Attendance Tracking**: Generates detailed attendance records for specific legislators
- **Multiple Output Formats**: Saves data as both JSON and Excel files
- **Flexible Execution**: Run via Makefile, bash scripts, or direct Python commands

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

**Full Analysis** (scrape + attendance record):
```bash
make judiciary LAST_NAME=Jordan
```

**Scraping Only**:
```bash
make scrape
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

```bash
python3 scrape_judiciary.py              # Scraping only
python3 attendance_record.py Jordan      # Attendance record only
```

## How it works:

1. **Scraping Phase**: The tool searches govinfo.gov for valid House Judiciary Committee hearing transcripts
2. **AI Analysis**: Each transcript is analyzed by Claude Sonnet 4 to extract structured information
3. **Data Storage**: Results are saved to `scrape_judiciary.json`
4. **Attendance Analysis**: For a specific legislator, generates an Excel file with their attendance record
5. **Output**: Creates both JSON data files and Excel reports

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

**Generate attendance record for Jim Jordan:**
```bash
make judiciary LAST_NAME=Jordan
```

**Just scrape hearings without generating attendance:**
```bash
make scrape
```

**Generate attendance for multiple legislators:**
```bash
make attendance LAST_NAME=Jordan
make attendance LAST_NAME=Raskin
make attendance LAST_NAME=Gaetz
```
