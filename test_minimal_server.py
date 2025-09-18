"""
Test script for the minimal working CricVerse server
"""

import requests
import time
import subprocess
import sys
import threading

def test_minimal_server():
    """Test the minimal working server"""
    print("🧪 Testing Minimal CricVerse Server")
    print("=" * 40)
    
    # Start server
    print("Starting minimal server...")
    process = subprocess.Popen([
        sys.executable, "app_minimal_working.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    time.sleep(5)
    
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"❌ Server failed to start:")
        print(f"STDOUT: {stdout.decode()}")
        print(f"STDERR: {stderr.decode()}")
        return False
    
    print("✅ Server started")
    
    # Test endpoints
    test_results = []
    
    # Test 1: Home page
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200 and "CricVerse" in response.text:
            print("✅ Home page working")
            test_results.append(True)
        else:
            print(f"❌ Home page failed: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ Home page error: {e}")
        test_results.append(False)
    
    # Test 2: API Status
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ API Status working")
                test_results.append(True)
            else:
                print("❌ API Status: Invalid response")
                test_results.append(False)
        else:
            print(f"❌ API Status failed: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ API Status error: {e}")
        test_results.append(False)
    
    # Test 3: CSRF Token
    try:
        response = requests.get("http://localhost:5000/api/csrf-token", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("csrf_token"):
                print("✅ CSRF Token working")
                test_results.append(True)
            else:
                print("❌ CSRF Token: Invalid response")
                test_results.append(False)
        else:
            print(f"❌ CSRF Token failed: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ CSRF Token error: {e}")
        test_results.append(False)
    
    # Clean up
    process.terminate()
    
    # Results
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Minimal server is working perfectly.")
        return True
    else:
        print("⚠️ Some tests failed.")
        return False

if __name__ == "__main__":
    test_minimal_server()