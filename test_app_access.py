#!/usr/bin/env python3
"""
Test Application Access
Simple script to test if we can access the running application
"""

import requests
import time

def test_app_access():
    """Test accessing the application"""
    urls_to_test = [
        'http://localhost:5000/',
        'http://localhost:5000/events',
        'http://localhost:5000/teams',
        'http://localhost:5000/stadiums',
        'http://localhost:5000/players'
    ]
    
    print("🔍 Testing application access...")
    print("=" * 50)
    
    for url in urls_to_test:
        try:
            print(f"Testing {url}...")
            response = requests.get(url, timeout=5)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Success - Content length: {len(response.text)} characters")
            else:
                print(f"   ❌ Failed - Status code: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection error - Application not accessible")
        except requests.exceptions.Timeout:
            print(f"   ❌ Timeout - Application not responding")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()

if __name__ == "__main__":
    test_app_access()