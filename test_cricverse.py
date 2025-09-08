#!/usr/bin/env python3
"""
CricVerse Feature Test Script
Tests the transformed CricVerse application endpoints and features
"""

import requests
import sys
import time
import json

def test_cricverse_features():
    """Test CricVerse application features"""
    base_url = "http://127.0.0.1:5000"
    
    print("🏏 CricVerse Feature Testing")
    print("=" * 50)
    
    # Test if server is running
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ CricVerse server is running!")
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to CricVerse server")
        print("   Make sure 'python app.py' is running")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Test key endpoints
    endpoints_to_test = [
        ("/", "Homepage with BBL branding"),
        ("/stadiums", "BBL Stadiums listing"),
        ("/teams", "BBL Teams page"),
        ("/players", "Player profiles"),
        ("/events", "Match schedule"),
        ("/concessions", "Vegetarian food court"),
        ("/login", "User authentication"),
        ("/register", "User registration"),
    ]
    
    print(f"\n🧪 Testing {len(endpoints_to_test)} key endpoints...")
    
    successful_tests = 0
    for endpoint, description in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint:<15} - {description}")
                successful_tests += 1
            else:
                print(f"❌ {endpoint:<15} - HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint:<15} - Error: {str(e)[:50]}...")
    
    # Test chatbot endpoint
    print(f"\n🤖 Testing AI Chatbot...")
    try:
        chatbot_data = {"message": "What BBL teams are available?"}
        response = requests.post(f"{base_url}/chatbot", 
                               json=chatbot_data, 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        if response.status_code == 200:
            bot_response = response.json()
            print(f"✅ Chatbot responded: {bot_response.get('response', 'No response')[:100]}...")
        else:
            print(f"❌ Chatbot error: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Chatbot error: {str(e)[:50]}...")
    
    # Test data seeding
    print(f"\n📊 Testing Database Content...")
    try:
        # Check if we can access teams data
        teams_response = requests.get(f"{base_url}/teams", timeout=5)
        if teams_response.status_code == 200 and "Adelaide Strikers" in teams_response.text:
            print("✅ BBL team data loaded successfully")
            successful_tests += 1
        else:
            print("⚠️  BBL team data may not be loaded")
            
        # Check if we can access stadiums data  
        stadiums_response = requests.get(f"{base_url}/stadiums", timeout=5)
        if stadiums_response.status_code == 200 and "Adelaide Oval" in stadiums_response.text:
            print("✅ Stadium data loaded successfully")
            successful_tests += 1
        else:
            print("⚠️  Stadium data may not be loaded")
            
    except Exception as e:
        print(f"❌ Data test error: {str(e)[:50]}...")
    
    # Check for dark mode CSS
    print(f"\n🎨 Testing CricVerse UI Theme...")
    try:
        homepage_response = requests.get(base_url, timeout=5)
        if "CricVerse" in homepage_response.text:
            print("✅ CricVerse branding detected")
            successful_tests += 1
        if "--primary-navy: #1a1b3a" in requests.get(f"{base_url}/static/css/unified.css", timeout=5).text:
            print("✅ BBL dark theme CSS loaded")
            successful_tests += 1
        if "chatbot-icon" in homepage_response.text:
            print("✅ AI chatbot interface present")
            successful_tests += 1
    except Exception as e:
        print(f"⚠️  UI theme test: {str(e)[:50]}...")
    
    print(f"\n📈 Test Results Summary:")
    print(f"   ✅ {successful_tests} features working correctly")
    print(f"   🔍 {len(endpoints_to_test) + 6 - successful_tests} features need attention")
    
    if successful_tests >= 8:
        print(f"\n🎉 CricVerse is working well! Great job!")
        print(f"   Visit http://127.0.0.1:5000 to explore the BBL cricket experience")
    elif successful_tests >= 5:
        print(f"\n👍 CricVerse is mostly functional with minor issues")
    else:
        print(f"\n⚠️  CricVerse needs some fixes before full functionality")
    
    return successful_tests >= 5

if __name__ == "__main__":
    try:
        success = test_cricverse_features()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n❌ Testing interrupted by user")
        sys.exit(1)
