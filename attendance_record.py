#!/usr/bin/env python3
"""
Generate attendance record for a specific legislator from scraped hearing data.
"""

import json
import pandas as pd
import sys
from datetime import datetime
from pathlib import Path

def find_legislator_in_hearing(hearing_data: dict, last_name: str) -> tuple:
    """
    Find legislator in hearing data and return their membership status and attendance.
    Returns: (is_member, subcommittee_name, is_present)
    """
    last_name_lower = last_name.lower()
    
    # Check if legislator is a committee/subcommittee member
    is_member = False
    subcommittee_name = ""
    
    for member in hearing_data.get('committee_members', []):
        member_name = member.get('name', '').lower()
        if last_name_lower in member_name:
            is_member = True
            subcommittee_name = hearing_data.get('subcommittee_name', '') or ""
            break
    
    # Check if legislator was present
    is_present = False
    if is_member:  # Only check attendance if they're a member
        for present_member in hearing_data.get('legislators_present', []):
            present_name = present_member.get('name', '').lower()
            if last_name_lower in present_name:
                is_present = True
                break
    
    return is_member, subcommittee_name, is_present

def generate_attendance_record(last_name: str):
    """Generate attendance record Excel file for specified legislator."""
    
    # Read the scraped hearing data
    json_file = "/Users/hanajafari/Desktop/MB Public Affairs/SOLO PROJECTS/house-judiciary/scrape_judiciary.json"
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            hearings_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file} not found. Please run scrape_judiciary.py first.")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {json_file}")
        return
    
    if not hearings_data:
        print("No hearing data found.")
        return
    
    # Process each hearing
    attendance_records = []
    found_as_member = False
    
    for hearing in hearings_data:
        is_member, subcommittee_name, is_present = find_legislator_in_hearing(hearing, last_name)
        
        if is_member:
            found_as_member = True
            attendance_status = "present" if is_present else "absent"
        else:
            attendance_status = "NOT A MEMBER"
        
        attendance_records.append({
            'Hearing Date': hearing.get('hearing_date', 'Not found'),
            'Hearing Title': hearing.get('hearing_title', 'Not found'),
            'URL': hearing.get('text_url', 'Not found'),
            'Subcommittee': subcommittee_name,
            'Attendance': attendance_status
        })
    
    # Create DataFrame
    df = pd.DataFrame(attendance_records)
    
    # Generate filename
    today = datetime.now().strftime("%d-%m-%Y")
    filename = f"{last_name}_judiciary_{today}.xlsx"
    output_path = f"/Users/hanajafari/Desktop/MB Public Affairs/SOLO PROJECTS/house-judiciary/{filename}"
    
    # Save to Excel
    try:
        df.to_excel(output_path, index=False)
        print(f"Attendance record saved to: {filename}")
        
        # Print summary
        if found_as_member:
            total_hearings = len([r for r in attendance_records if r['Attendance'] != 'NOT A MEMBER'])
            present_count = len([r for r in attendance_records if r['Attendance'] == 'present'])
            print(f"Summary for {last_name}:")
            print(f"  Total hearings as member: {total_hearings}")
            print(f"  Hearings attended: {present_count}")
            print(f"  Attendance rate: {present_count}/{total_hearings}")
        else:
            print(f"Warning: {last_name} was not found as a committee or subcommittee member in any hearings.")
            
    except Exception as e:
        print(f"Error saving Excel file: {e}")

def main():
    """Main execution function."""
    if len(sys.argv) != 2:
        print("Usage: python3 attendance_record.py <legislator_last_name>")
        print("Example: python3 attendance_record.py Jordan")
        return
    
    last_name = sys.argv[1]
    generate_attendance_record(last_name)

if __name__ == "__main__":
    main()
