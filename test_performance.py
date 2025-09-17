#!/usr/bin/env python3
"""
Quick Performance Test for CricVerse Home Page
Tests loading times and basic functionality
"""

import time
import requests
from datetime import datetime

def test_home_page_performance():
    """Test home page loading performance"""
    print("[START] Testing CricVerse Home Page Performance")
    print(f"[TIME] Started: {datetime.now().strftime('%H:%M:%S')}")
    
    base_url = "http://localhost:5000"
    
    # Test 1: Basic connectivity
    print("\n1. Testing basic connectivity...")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/", timeout=10)
        load_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"[PASS] Home page loaded successfully")
            print(f"[PERF] Load time: {load_time:.2f} seconds")
            print(f"[STATS] Response size: {len(response.content)} bytes")
            
            # Check for key content
            content = response.text.lower()
            if "big bash" in content:
                print("[PASS] BBL content found")
            if "cricverse" in content:
                print("[PASS] CricVerse branding found")
            if "error" in content and "database" in content:
                print("[WARN]  Database fallback mode detected (expected)")
        else:
            print(f"[FAIL] HTTP Error: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"[FAIL] Connection failed: {e}")
        return False
    
    # Test 2: Static resources
    print("\n2. Testing static resources...")
    static_resources = [
        "/static/css/unified.css",
        "/static/css/bbl-enhanced.css", 
        "/static/js/main.js"
    ]
    
    for resource in static_resources:
        try:
            start_time = time.time()
            response = requests.head(f"{base_url}{resource}", timeout=5)
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"[PASS] {resource} - {load_time:.2f}s")
            else:
                print(f"[WARN]  {resource} - {response.status_code}")
        except:
            print(f"[FAIL] {resource} - Failed to load")
    
    # Test 3: Multiple requests (stress test)
    print("\n3. Testing with multiple requests...")
    total_time = 0
    successful_requests = 0
    
    for i in range(5):
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}/", timeout=5)
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                total_time += load_time
                successful_requests += 1
                print(f"   Request {i+1}: {load_time:.2f}s")
            else:
                print(f"   Request {i+1}: Failed ({response.status_code})")
        except:
            print(f"   Request {i+1}: Timeout/Error")
    
    if successful_requests > 0:
        avg_time = total_time / successful_requests
        print(f"[UP] Average load time: {avg_time:.2f}s")
        print(f"[PASS] Success rate: {successful_requests}/5 ({successful_requests*20}%)")
        
        # Performance evaluation
        if avg_time < 1.0:
            print("[GOOD] EXCELLENT performance")
        elif avg_time < 2.0:
            print("[OK] GOOD performance")
        elif avg_time < 5.0:
            print("[SLOW] ACCEPTABLE performance")
        else:
            print("[BAD] SLOW performance - optimization needed")
    
    print(f"\n[PASS] Test completed: {datetime.now().strftime('%H:%M:%S')}")
    return True

if __name__ == "__main__":
    test_home_page_performance()