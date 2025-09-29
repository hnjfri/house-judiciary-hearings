#!/usr/bin/env python3
"""
Scrape House Judiciary Committee hearing transcripts from GovInfo website
and extract structured information using Claude Sonnet 4.
"""

import os
import json
import time
from typing import Dict, List, Optional
import anthropic
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from dotenv import load_dotenv
import re


class HearingTranscriptScraper:
    def __init__(self, api_key: Optional[str] = None, govinfo_api_key: Optional[str] = None):
        """Initialize the scraper with Anthropic API key and optional GovInfo API key."""
        # Load environment variables from .env file
        load_dotenv()
        
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Please:\n"
                "1. Copy .env.template to .env\n"
                "2. Add your Anthropic API key to the .env file"
            )
        
        # GovInfo API key for official API access
        self.govinfo_api_key = govinfo_api_key or os.getenv('GOVINFO_API_KEY')
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    
    def scrape_with_govinfo_api(self) -> List[Dict]:
        """Use the official GovInfo API to get all House Judiciary Committee hearings."""
        if not self.govinfo_api_key:
            print("GovInfo API key not available, falling back to number-based search...")
            return self.find_all_hearing_urls_fallback()
        
        api_url = "https://api.govinfo.gov/search"
        
        print("Using official GovInfo API to find hearings...")
        print("This is the fastest and most reliable method!")
        
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Api-Key': self.govinfo_api_key
        }
        
        payload = {
            "query": "collection:CHRG congress:119 Judiciary",
            "pageSize": 1000,
            "offsetMark": "*",
            "sorts": [
                {
                    "field": "dateIssued",
                    "sortOrder": "DESC"
                }
            ],
            "resultLevel": "package"
        }
        
        try:
            print("Making API request to GovInfo...")
            response = self.session.post(api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'results' not in data:
                print("No results found in API response")
                return self.find_all_hearing_urls_fallback()
            
            results = data['results']
            count = data.get('count', len(results))
            print(f"API returned {len(results)} results (total count: {count})")
            
            valid_hearings = []
            found_hearing_ids = set()
            
            for package in results:
                package_id = package.get('packageId', '')
                
                # Extract hearing number from package ID
                match = re.search(r'CHRG-119hhrg(\d+)', package_id)
                if match:
                    hearing_number = int(match.group(1))
                    hearing_id = f"{hearing_number:05d}"
                    
                    if hearing_id not in found_hearing_ids:
                        found_hearing_ids.add(hearing_id)
                        
                        # Get title and other metadata from API response
                        title = package.get('title', f'House Judiciary Committee Hearing {hearing_id}')
                        date_issued = package.get('dateIssued', 'Unknown')
                        
                        # Construct URLs
                        hearing_url = f"https://www.govinfo.gov/content/pkg/CHRG-119hhrg{hearing_id}"
                        text_url = f"https://www.govinfo.gov/content/pkg/CHRG-119hhrg{hearing_id}/html/CHRG-119hhrg{hearing_id}.htm"
                        
                        valid_hearings.append({
                            'title': title,
                            'url': hearing_url,
                            'text_url': text_url,
                            'hearing_number': hearing_number,
                            'date_issued': date_issued,
                            'package_id': package_id
                        })
                        
                        print(f"Found hearing: CHRG-119hhrg{hearing_id} - {title[:60]}...")
            
            # Sort by hearing number for consistent processing order
            valid_hearings.sort(key=lambda x: x['hearing_number'])
            
            print(f"\nGovInfo API search complete!")
            print(f"Found {len(valid_hearings)} House Judiciary Committee hearings")
            
            return valid_hearings
            
        except Exception as e:
            print(f"Error with GovInfo API: {e}")
            print("Falling back to number-based search method...")
            return self.find_all_hearing_urls_fallback()
    
    def scrape_collection_page(self) -> List[Dict]:
        """Scrape hearings using the GovInfo API method."""
        return self.scrape_with_govinfo_api()
    
    def find_all_hearing_urls_fallback(self) -> List[Dict]:
        """Fallback method using number-based search if collection page scraping fails."""
        print("Using fallback number-based search method...")
        
        valid_hearings = []
        
        # Based on known hearings, search from 58400 to 61000 to cover full range
        start_num = 58400
        end_num = 61000  # Beyond the latest known hearing (60840)
        
        print(f"Starting comprehensive search from {start_num} to {end_num}")
        print("Note: This will take ~5 minutes due to large gaps between hearing numbers")
        
        for current_num in range(start_num, end_num + 1):
            # Format with leading zeros for consistency
            hearing_id = f"{current_num:05d}"
            text_url = f"https://www.govinfo.gov/content/pkg/CHRG-119hhrg{hearing_id}/html/CHRG-119hhrg{hearing_id}.htm"
            
            if self.test_url_exists(text_url):
                hearing_url = f"https://www.govinfo.gov/content/pkg/CHRG-119hhrg{hearing_id}"
                valid_hearings.append({
                    'title': f'House Judiciary Committee Hearing {hearing_id}',
                    'url': hearing_url,
                    'text_url': text_url,
                    'hearing_number': current_num
                })
                print(f"Found valid hearing: CHRG-119hhrg{hearing_id} (Total found: {len(valid_hearings)})")
            
            # Progress indicator every 100 numbers
            if (current_num - start_num + 1) % 100 == 0:
                progress = ((current_num - start_num + 1) / (end_num - start_num + 1)) * 100
                print(f"  Progress: {progress:.1f}% - Searched up to {hearing_id}, found {len(valid_hearings)} hearings")
            
            # Add small delay to be respectful to the server
            time.sleep(0.1)
        
        print(f"\nSearch complete! Found {len(valid_hearings)} total hearings")
        print(f"Searched range: {start_num:05d} to {end_num:05d}")
        
        return valid_hearings
    
    def find_all_hearing_urls(self) -> List[Dict]:
        """Find ALL valid hearing URLs using GovInfo API (with fallback to number search)."""
        print("Searching for ALL valid hearing URLs in 119th Congress...")
        
        return self.scrape_collection_page()
    
    
    def test_url_exists(self, url: str) -> bool:
        """Test if a URL exists by making a HEAD request."""
        try:
            response = self.session.head(url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def fetch_transcript_text(self, text_url: str) -> str:
        """Fetch transcript text from URL."""
        try:
            print(f"Fetching transcript from: {text_url}")
            response = self.session.get(text_url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script, style, and other non-content elements
            for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
                element.decompose()
            
            # Extract text content
            text = soup.get_text()
            
            # Clean up the text - preserve structure but remove excessive whitespace
            lines = []
            for line in text.splitlines():
                cleaned_line = line.strip()
                if cleaned_line:  # Only keep non-empty lines
                    lines.append(cleaned_line)
            
            text = '\n'.join(lines)
            
            print(f"Extracted {len(text)} characters of text")
            
            # Validate that we got actual hearing content
            if len(text) < 1000:
                print("Warning: Text content seems too short, might be an error page")
                return ""
            
            # Simple validation - GovInfo API should have filtered correctly
            # Just do a basic sanity check without AI
            if not self.is_judiciary_hearing(text):
                print("Warning: Does not appear to be a Judiciary Committee hearing, skipping...")
                return ""
            
            return text
            
        except Exception as e:
            print(f"Error fetching transcript text: {e}")
            return ""
    
    def is_judiciary_hearing(self, text: str) -> bool:
        """Simple check to validate if this is a Judiciary Committee hearing without using AI."""
        text_upper = text.upper()
        
        # Must have one of these primary indicators
        primary_indicators = [
            'HOUSE COMMITTEE ON THE JUDICIARY',
            'COMMITTEE ON THE JUDICIARY',
            'JUDICIARY COMMITTEE'
        ]
        
        # Should NOT have strong indicators of other committees
        other_committee_indicators = [
            'COMMITTEE ON OVERSIGHT AND ACCOUNTABILITY',
            'COMMITTEE ON TRANSPORTATION AND INFRASTRUCTURE',
            'COMMITTEE ON ENERGY AND COMMERCE',
            'COMMITTEE ON FOREIGN AFFAIRS',
            'COMMITTEE ON VETERANS\' AFFAIRS',
            'COMMITTEE ON WAYS AND MEANS',
            'COMMITTEE ON NATURAL RESOURCES',
            'COMMITTEE ON HOUSE ADMINISTRATION',
            'COMMITTEE ON HOMELAND SECURITY',
            'COMMITTEE ON ARMED SERVICES',
            'COMMITTEE ON FINANCIAL SERVICES'
        ]
        
        has_judiciary_content = any(indicator in text_upper for indicator in primary_indicators)
        has_other_committee = any(indicator in text_upper for indicator in other_committee_indicators)
        
        return has_judiciary_content and not has_other_committee
    
    def extract_hearing_info(self, transcript_text: str, text_url: str) -> Dict:
        """Use Claude to extract specific hearing information from transcript text."""
        
        print("Using Anthropic API to extract hearing data...")
        
        prompt = f"""
        Please analyze this House Judiciary Committee hearing transcript and extract the following specific information:

        1. **Date of the hearing** - Find the exact date when this hearing took place
        2. **Title of the hearing** - The official title or subject of the hearing
        3. **URL of the valid hearing transcript text** - Use this URL: {text_url}
        4. **Subcommittee name** - If this is a subcommittee hearing, provide the full subcommittee name. If it's a full committee hearing, return null.
        5. **Committee/Subcommittee members** - If it's a subcommittee hearing, list the subcommittee members. If it's a full committee hearing, list all House Judiciary Committee members.
        6. **Legislators present** - List only the legislators who were actually present at this specific hearing AND who are also listed as committee/subcommittee members. Do not include anyone as "present" if they are not also a committee/subcommittee member.

        Please format your response as a JSON object with the following structure:
        {{
            "hearing_date": "YYYY-MM-DD or descriptive date",
            "hearing_title": "Official title of the hearing",
            "text_url": "{text_url}",
            "subcommittee_name": "Full subcommittee name or null",
            "committee_members": [
                {{
                    "name": "Full Name",
                    "party": "R/D/I",
                    "state": "State abbreviation",
                    "role": "Chairman/Ranking Member/Member"
                }}
            ],
            "legislators_present": [
                {{
                    "name": "Full Name", 
                    "party": "R/D/I",
                    "state": "State abbreviation",
                    "role": "Chairman/Ranking Member/Member"
                }}
            ]
        }}

        IMPORTANT: Only include legislators in "legislators_present" if they appear in BOTH the attendance records AND the committee_members list. If someone attended but is not a committee member, do not include them.

        If you cannot find specific information, use "Not found" as the value. Be thorough in your analysis.

        Here is the transcript text:

        {transcript_text}
        """

        try:
            # Add retry logic for rate limiting
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=4000,
                        temperature=0,
                        messages=[
                            {
                                "role": "user", 
                                "content": prompt
                            }
                        ]
                    )
                    break  # Success, exit retry loop
                    
                except Exception as api_error:
                    if "rate_limit_error" in str(api_error) and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 60  # 60, 120, 180 seconds
                        print(f"Rate limit hit, waiting {wait_time} seconds before retry {attempt + 2}/{max_retries}...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise api_error
            
            # Extract JSON from response
            response_text = response.content[0].text
            
            # Try to find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                # If no JSON found, return the raw response
                return {"raw_response": response_text}
                
        except Exception as e:
            raise Exception(f"Error calling Anthropic API: {e}")
    
    def extract_hearing_number(self, url: str) -> int:
        """Extract hearing number from URL."""
        import re
        match = re.search(r'CHRG-119hhrg(\d+)', url)
        return int(match.group(1)) if match else 0
    
    def load_existing_data(self, output_file: str) -> List[Dict]:
        """Load existing hearing data if file exists."""
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                print("Warning: Could not load existing data, starting fresh")
                return []
        return []
    
    def save_data(self, data: List[Dict], output_file: str):
        """Save data to JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def process_all_hearings_batched(self, batch_size: int = 3, output_file: str = None) -> List[Dict]:
        """Process ALL hearings in batches with resumption capability."""
        if output_file is None:
            output_file = "/Users/hanajafari/Desktop/MB Public Affairs/SOLO PROJECTS/house-judiciary/scrape_judiciary.json"
        
        print("Starting comprehensive hearing analysis...")
        print("Step 1: Using FREE GovInfo API to find Judiciary Committee hearings")
        print("Step 2: Simple text validation (no AI)")
        print("Step 3: AI extraction only for confirmed Judiciary hearings")
        print("This approach minimizes expensive Anthropic API calls!")
        print()
        
        # Load existing data if resuming
        existing_data = self.load_existing_data(output_file)
        processed_numbers = {self.extract_hearing_number(h.get('source_url', '')) for h in existing_data}
        
        print(f"Found {len(existing_data)} previously processed hearings")
        
        # Find all available hearings
        all_hearings = self.find_all_hearing_urls()
        
        # Filter out already processed hearings
        new_hearings = [h for h in all_hearings if h['hearing_number'] not in processed_numbers]
        
        print(f"Found {len(new_hearings)} new hearings to process")
        print(f"Total hearings available: {len(all_hearings)}")
        
        if not new_hearings:
            print("All hearings already processed!")
            return existing_data
        
        # Process in batches
        total_batches = (len(new_hearings) - 1) // batch_size + 1
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(new_hearings))
            batch = new_hearings[start_idx:end_idx]
            
            print(f"\nProcessing Batch {batch_num + 1}/{total_batches} ({len(batch)} hearings)")
            print("=" * 60)
            
            batch_results = []
            
            for i, hearing in enumerate(batch, 1):
                print(f"\n--- Processing Hearing {i}/{len(batch)} in Batch {batch_num + 1} ---")
                print(f"Title: {hearing['title']}")
                print(f"URL: {hearing['url']}")
                
                try:
                    # Fetch transcript text
                    print("Fetching transcript text...")
                    transcript_text = self.fetch_transcript_text(hearing['text_url'])
                    
                    if not transcript_text:
                        print("Failed to fetch transcript text, skipping...")
                        continue
                    
                    print("Transcript validated as Judiciary Committee hearing")
                    
                    # Extract hearing information using AI
                    hearing_info = self.extract_hearing_info(transcript_text, hearing['text_url'])
                    hearing_info['source_url'] = hearing['url']
                    hearing_info['hearing_number'] = hearing['hearing_number']
                    
                    batch_results.append(hearing_info)
                    existing_data.append(hearing_info)
                    
                    print(f"Successfully processed: {hearing_info.get('hearing_title', 'Unknown')}")
                    
                    # Save after each successful processing (for resumption)
                    self.save_data(existing_data, output_file)
                    
                except Exception as e:
                    print(f"Error processing hearing {hearing['hearing_number']}: {e}")
                    continue
                
                # Add delay between API calls to respect rate limits
                if i < len(batch):
                    print("Waiting 15 seconds before next hearing...")
                    time.sleep(15)
            
            print(f"\nCompleted batch {batch_num + 1}/{total_batches}")
            print(f"Progress: {len(existing_data)}/{len(all_hearings)} total hearings processed")
            
            # Longer delay between batches
            if batch_num < total_batches - 1:
                print("Waiting 60 seconds before next batch...")
                time.sleep(60)
        
        print(f"\nAll processing complete!")
        print(f"Final count: {len(existing_data)} hearings processed")
        
        return existing_data
    
    def process_hearings(self, limit: int = 5) -> List[Dict]:
        """Legacy method for backward compatibility - processes limited number of hearings."""
        print(f"Processing up to {limit} hearings...")
        
        # Get hearing links using the API-based approach
        all_hearings = self.find_all_hearing_urls()
        hearing_links = all_hearings[:limit]
        
        if not hearing_links:
            print("No hearing links found")
            return []
        
        results = []
        
        for i, hearing in enumerate(hearing_links, 1):
            print(f"\n--- Processing Hearing {i}/{len(hearing_links)} ---")
            print(f"Title: {hearing['title']}")
            print(f"URL: {hearing['url']}")
            
            # Fetch transcript text
            transcript_text = self.fetch_transcript_text(hearing['text_url'])
            
            if not transcript_text:
                print("Failed to fetch transcript text, skipping...")
                continue
            
            # Extract hearing information
            try:
                hearing_info = self.extract_hearing_info(transcript_text, hearing['text_url'])
                hearing_info['source_url'] = hearing['url']
                results.append(hearing_info)
                
                print(f"Successfully processed hearing: {hearing_info.get('hearing_title', 'Unknown')}")
                
            except Exception as e:
                print(f"Error processing hearing: {e}")
                continue
            
            # Add delay between API calls to respect rate limits
            if i < len(hearing_links):
                print("Waiting 15 seconds before next hearing...")
                time.sleep(15)
        
        return results

def main():
    """Main execution function with command-line options."""
    import sys
    
    # Check for command-line arguments
    mode = "comprehensive"  # Default to comprehensive mode
    batch_size = 3
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--legacy" or sys.argv[1] == "-l":
            mode = "legacy"
        elif sys.argv[1] == "--batch-size" or sys.argv[1] == "-b":
            if len(sys.argv) > 2:
                try:
                    batch_size = int(sys.argv[2])
                except ValueError:
                    print("Invalid batch size. Using default of 10.")
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("House Judiciary Committee Hearing Scraper")
            print("\nUsage:")
            print("  python3 scrape_judiciary.py                    # Process ALL hearings (comprehensive mode)")
            print("  python3 scrape_judiciary.py --legacy           # Process only 5 hearings (legacy mode)")
            print("  python3 scrape_judiciary.py --batch-size 20    # Set batch size for processing")
            print("  python3 scrape_judiciary.py --help             # Show this help")
            print("\nComprehensive mode will:")
            print("  - Find ALL hearings in the 119th Congress")
            print("  - Process them in batches with resumption capability")
            print("  - Save progress after each hearing")
            print("  - Can be interrupted and resumed")
            return
    
    try:
        # Initialize scraper
        scraper = HearingTranscriptScraper()
        
        output_file = "/Users/hanajafari/Desktop/MB Public Affairs/SOLO PROJECTS/house-judiciary/scrape_judiciary.json"
        
        if mode == "comprehensive":
            print("Running in COMPREHENSIVE mode - will process ALL hearings")
            print(f"Batch size: {batch_size}")
            print("Tip: You can interrupt (Ctrl+C) and resume later - progress is saved!")
            print()
            
            # Process all hearings with batching and resumption
            hearing_results = scraper.process_all_hearings_batched(batch_size=batch_size, output_file=output_file)
            
        else:
            print("Running in LEGACY mode - will process 5 hearings")
            
            # Process limited hearings (legacy behavior)
        hearing_results = scraper.process_hearings(limit=5)
        
        if not hearing_results:
            print("No hearings were successfully processed")
            return
        
        # Save results to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(hearing_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print("SCRAPING RESULTS")
        print("="*60)
        print(f"Successfully processed {len(hearing_results)} hearings")
        print(f"Results saved to: {output_file}")
        
        # Print summary
        for i, hearing in enumerate(hearing_results[:10], 1):  # Show first 10
            print(f"\n{i}. {hearing.get('hearing_title', 'Unknown Title')}")
            print(f"   Date: {hearing.get('hearing_date', 'Unknown')}")
            print(f"   Subcommittee: {hearing.get('subcommittee_name', 'Full Committee')}")
            print(f"   Present: {len(hearing.get('legislators_present', []))} legislators")
        
        if len(hearing_results) > 10:
            print(f"\n... and {len(hearing_results) - 10} more hearings")
        
        print(f"\nTotal hearings processed: {len(hearing_results)}")
        
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user")
        print("Progress has been saved - you can resume by running the script again")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
