#!/usr/bin/env python3
"""
Test script to verify that the website styling is working properly
"""

import requests
import re
from bs4 import BeautifulSoup

def test_website_styling():
    """Test if the website styling is working properly"""
    print("Testing CricVerse Website Styling...")
    print("=" * 50)
    
    try:
        # Test home page
        response = requests.get("http://localhost:5000/", timeout=10)
        
        if response.status_code == 200:
            print("✅ Home page loads successfully")
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for CSS files
            css_files = soup.find_all('link', rel='stylesheet')
            print(f"✅ Found {len(css_files)} CSS files")
            
            # Check for glass-header class
            header = soup.find('header', class_='glass-header')
            if header:
                print("✅ Glass header found")
            else:
                print("❌ Glass header not found")
            
            # Check for main content
            main_content = soup.find('main', class_='main-content')
            if main_content:
                print("✅ Main content found")
            else:
                print("❌ Main content not found")
            
            # Check for navbar
            navbar = soup.find('nav', class_='navbar')
            if navbar:
                print("✅ Navbar found")
            else:
                print("❌ Navbar not found")
            
            # Check for BBL Action Hub
            action_hub = soup.find('section', class_='action-hub-section')
            if action_hub:
                print("✅ BBL Action Hub found")
            else:
                print("❌ BBL Action Hub not found")
            
            # Check for teams carousel
            teams_carousel = soup.find('div', class_='teams-carousel-wrapper')
            if teams_carousel:
                print("✅ Teams carousel found")
            else:
                print("❌ Teams carousel not found")
            
            print("\n" + "=" * 50)
            print("🎉 Website styling test completed!")
            
        else:
            print(f"❌ Home page returned status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing website: {e}")

if __name__ == "__main__":
    test_website_styling()
