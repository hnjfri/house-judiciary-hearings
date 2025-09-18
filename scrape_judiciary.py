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
    
    def find_hearing_urls(self, limit: int = 5) -> List[Dict]:
        """Systematically find valid hearing URLs by testing number ranges."""
        print("Searching for valid hearing URLs...")
        
        valid_hearings = []
        
        # Test range of hearing numbers
        for num in range(50000, 70000, 50):  # Test every 50th number for efficiency
            if len(valid_hearings) >= limit:
                break
                
            text_url = f"https://www.govinfo.gov/content/pkg/CHRG-119hhrg{num}/html/CHRG-119hhrg{num}.htm"
            
            if self.test_url_exists(text_url):
                hearing_url = f"https://www.govinfo.gov/content/pkg/CHRG-119hhrg{num}"
                valid_hearings.append({
                    'title': f'House Judiciary Committee Hearing {num}',
                    'url': hearing_url,
                    'text_url': text_url
                })
                print(f"Found valid hearing: CHRG-119hhrg{num}")
        
        print(f"Found {len(valid_hearings)} valid hearings")
        return valid_hearings
    
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
    
    def process_hearings(self, limit: int = 5) -> List[Dict]:
        """Main method to process multiple hearings."""
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
    """Main execution function."""
    try:
        # Initialize scraper
        scraper = HearingTranscriptScraper()
        
        # Process hearings
        hearing_results = scraper.process_hearings(limit=5)
        
        if not hearing_results:
            print("No hearings were successfully processed")
            return
        
        # Save results to JSON file
        output_file = "/Users/hanajafari/Desktop/MB Public Affairs/SOLO PROJECTS/house-judiciary/scrape_judiciary.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(hearing_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print("SCRAPING RESULTS")
        print("="*60)
        print(f"Successfully processed {len(hearing_results)} hearings")
        print(f"Results saved to: {output_file}")
        
        # Print summary
        for i, hearing in enumerate(hearing_results, 1):
            print(f"\n{i}. {hearing.get('hearing_title', 'Unknown Title')}")
            print(f"   Date: {hearing.get('hearing_date', 'Unknown')}")
            print(f"   Subcommittee: {hearing.get('subcommittee_name', 'Full Committee')}")
            print(f"   Present: {len(hearing.get('legislators_present', []))} legislators")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
