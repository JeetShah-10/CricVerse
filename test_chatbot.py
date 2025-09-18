"""
Test AI chatbot functionality
"""

from app import app
import json

def test_chatbot():
    """Test the AI chatbot API"""
    print("=" * 50)
    print("Testing AI Chatbot Functionality")
    print("=" * 50)
    
    with app.test_client() as client:
        try:
            # Test 1: Basic chatbot response
            print("1. Testing basic chatbot response...")
            
            payload = {"message": "Hello"}
            response = client.post(
                '/api/chat',
                json=payload,
                content_type='application/json'
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('success'):
                    print("PASS: Chatbot responding")
                    print(f"Response: {data.get('response', 'No response')[:100]}...")
                    print(f"Confidence: {data.get('confidence', 'N/A')}")
                    print(f"Model: {data.get('model', 'N/A')}")
                else:
                    print(f"FAIL: Invalid response format: {data}")
            else:
                print(f"FAIL: HTTP error {response.status_code}")
                print(f"Response: {response.get_data(as_text=True)}")
            
            # Test 2: Cricket-related query
            print("\n2. Testing cricket-related query...")
            
            payload = {"message": "Tell me about BBL cricket"}
            response = client.post(
                '/api/chat',
                json=payload,
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('success'):
                    print("PASS: Cricket query responded")
                    print(f"Response: {data.get('response', 'No response')[:150]}...")
                else:
                    print(f"FAIL: Invalid cricket response: {data}")
            else:
                print(f"FAIL: Cricket query failed with status {response.status_code}")
            
            # Test 3: Booking-related query
            print("\n3. Testing booking-related query...")
            
            payload = {"message": "How do I book tickets?"}
            response = client.post(
                '/api/chat',
                json=payload,
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('success'):
                    print("PASS: Booking query responded")
                    intent = data.get('intent', 'unknown')
                    quick_actions = data.get('quick_actions', [])
                    print(f"Detected intent: {intent}")
                    print(f"Quick actions: {len(quick_actions)} available")
                else:
                    print(f"FAIL: Invalid booking response: {data}")
            else:
                print(f"FAIL: Booking query failed with status {response.status_code}")
            
            # Test 4: Chat suggestions
            print("\n4. Testing chat suggestions...")
            
            response = client.get('/api/chat/suggestions?type=general')
            
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('success'):
                    suggestions = data.get('suggestions', [])
                    print(f"PASS: Got {len(suggestions)} suggestions")
                    for i, suggestion in enumerate(suggestions[:3], 1):
                        print(f"  {i}. {suggestion}")
                else:
                    print(f"FAIL: Invalid suggestions response: {data}")
            else:
                print(f"FAIL: Suggestions failed with status {response.status_code}")
            
            # Test 5: Error handling
            print("\n5. Testing error handling...")
            
            # Test with invalid JSON
            response = client.post(
                '/api/chat',
                data="invalid json",
                content_type='application/json'
            )
            
            if response.status_code == 400:
                print("PASS: Handles invalid JSON properly")
            else:
                print(f"WARN: Unexpected response to invalid JSON: {response.status_code}")
            
            # Test with empty message
            payload = {"message": ""}
            response = client.post(
                '/api/chat',
                json=payload,
                content_type='application/json'
            )
            
            if response.status_code == 400:
                print("PASS: Handles empty message properly")
            else:
                print(f"WARN: Unexpected response to empty message: {response.status_code}")
            
            print("\n" + "=" * 50)
            print("Chatbot Testing Complete")
            print("=" * 50)
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_chatbot()