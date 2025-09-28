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
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the scraper with Anthropic API key."""
        # Load environment variables from .env file
        load_dotenv()
        
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Please:\n"
                "1. Copy .env.template to .env\n"
                "2. Add your Anthropic API key to the .env file"
            )
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def find_all_hearing_urls(self) -> List[Dict]:
        """Find ALL valid hearing URLs by testing sequential numbers."""
        print("Searching for ALL valid hearing URLs in 119th Congress...")
        
        valid_hearings = []
        consecutive_failures = 0
        max_consecutive_failures = 200  # Stop after 200 consecutive failures
        
        # Start from a reasonable lower bound for 119th Congress
        start_num = 50000
        current_num = start_num
        
        print(f"Starting search from hearing number {start_num}")
        
        while consecutive_failures < max_consecutive_failures:
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
                consecutive_failures = 0  # Reset counter
                print(f"✓ Found valid hearing: CHRG-119hhrg{hearing_id} (Total found: {len(valid_hearings)})")
            else:
                consecutive_failures += 1
                if consecutive_failures % 50 == 0:
                    print(f"  Searched {consecutive_failures} consecutive numbers without finding hearings...")
            
            current_num += 1
            
            # Add small delay to be respectful to the server
            time.sleep(0.1)
        
        print(f"\n🎉 Search complete! Found {len(valid_hearings)} total hearings")
        print(f"Search ended after {consecutive_failures} consecutive failures at number {current_num}")
        
        return valid_hearings
    
    def find_hearing_urls(self, limit: int = 5) -> List[Dict]:
        """Legacy method for backward compatibility - finds limited number of hearings."""
        all_hearings = self.find_all_hearing_urls()
        return all_hearings[:limit]
    
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
            elif 'COMMITTEE ON THE JUDICIARY' not in text.upper():
                print("Warning: Text doesn't appear to be a Judiciary Committee hearing")
                return ""
            
            return text
            
        except Exception as e:
            print(f"Error fetching transcript text: {e}")
            return ""
    
    def extract_hearing_info(self, transcript_text: str, text_url: str) -> Dict:
        """Use Claude to extract specific hearing information from transcript text."""
        
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
    
    def process_all_hearings_batched(self, batch_size: int = 10, output_file: str = None) -> List[Dict]:
        """Process ALL hearings in batches with resumption capability."""
        if output_file is None:
            output_file = "/Users/hanajafari/Desktop/MB Public Affairs/SOLO PROJECTS/house-judiciary/scrape_judiciary.json"
        
        print("🚀 Starting comprehensive hearing analysis...")
        
        # Load existing data if resuming
        existing_data = self.load_existing_data(output_file)
        processed_numbers = {self.extract_hearing_number(h.get('source_url', '')) for h in existing_data}
        
        print(f"📂 Found {len(existing_data)} previously processed hearings")
        
        # Find all available hearings
        all_hearings = self.find_all_hearing_urls()
        
        # Filter out already processed hearings
        new_hearings = [h for h in all_hearings if h['hearing_number'] not in processed_numbers]
        
        print(f"📋 Found {len(new_hearings)} new hearings to process")
        print(f"📊 Total hearings available: {len(all_hearings)}")
        
        if not new_hearings:
            print("✅ All hearings already processed!")
            return existing_data
        
        # Process in batches
        total_batches = (len(new_hearings) - 1) // batch_size + 1
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(new_hearings))
            batch = new_hearings[start_idx:end_idx]
            
            print(f"\n📦 Processing Batch {batch_num + 1}/{total_batches} ({len(batch)} hearings)")
            print("=" * 60)
            
            batch_results = []
            
            for i, hearing in enumerate(batch, 1):
                print(f"\n--- Processing Hearing {i}/{len(batch)} in Batch {batch_num + 1} ---")
                print(f"Title: {hearing['title']}")
                print(f"URL: {hearing['url']}")
                
                try:
                    # Fetch transcript text
                    transcript_text = self.fetch_transcript_text(hearing['text_url'])
                    
                    if not transcript_text:
                        print("❌ Failed to fetch transcript text, skipping...")
                        continue
                    
                    # Extract hearing information
                    hearing_info = self.extract_hearing_info(transcript_text, hearing['text_url'])
                    hearing_info['source_url'] = hearing['url']
                    hearing_info['hearing_number'] = hearing['hearing_number']
                    
                    batch_results.append(hearing_info)
                    existing_data.append(hearing_info)
                    
                    print(f"✅ Successfully processed: {hearing_info.get('hearing_title', 'Unknown')}")
                    
                    # Save after each successful processing (for resumption)
                    self.save_data(existing_data, output_file)
                    
                except Exception as e:
                    print(f"❌ Error processing hearing {hearing['hearing_number']}: {e}")
                    continue
                
                # Add delay between API calls to respect rate limits
                if i < len(batch):
                    print("⏳ Waiting 3 seconds before next hearing...")
                    time.sleep(3)
            
            print(f"\n✅ Completed batch {batch_num + 1}/{total_batches}")
            print(f"📈 Progress: {len(existing_data)}/{len(all_hearings)} total hearings processed")
            
            # Longer delay between batches
            if batch_num < total_batches - 1:
                print("⏳ Waiting 10 seconds before next batch...")
                time.sleep(10)
        
        print(f"\n🎉 All processing complete!")
        print(f"📊 Final count: {len(existing_data)} hearings processed")
        
        return existing_data
    
    def process_hearings(self, limit: int = 5) -> List[Dict]:
        """Legacy method for backward compatibility - processes limited number of hearings."""
        print(f"Processing up to {limit} hearings...")
        
        # Get hearing links
        hearing_links = self.find_hearing_urls(limit)
        
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
                print("Waiting 2 seconds before next hearing...")
                time.sleep(2)
        
        return results

def main():
    """Main execution function with command-line options."""
    import sys
    
    # Check for command-line arguments
    mode = "comprehensive"  # Default to comprehensive mode
    batch_size = 10
    
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
            print("🚀 Running in COMPREHENSIVE mode - will process ALL hearings")
            print(f"📦 Batch size: {batch_size}")
            print("💡 Tip: You can interrupt (Ctrl+C) and resume later - progress is saved!")
            print()
            
            # Process all hearings with batching and resumption
            hearing_results = scraper.process_all_hearings_batched(batch_size=batch_size, output_file=output_file)
            
        else:
            print("🔄 Running in LEGACY mode - will process 5 hearings")
            
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
        
        print(f"\n📊 Total hearings processed: {len(hearing_results)}")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Processing interrupted by user")
        print("💾 Progress has been saved - you can resume by running the script again")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
