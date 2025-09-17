#!/usr/bin/env python3
"""
Test AI Chatbot after applying fixes
Verifies that the simplified chatbot is working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

def test_simplified_chatbot():
    """Test the simplified chatbot"""
    print("🤖 Testing Fixed AI Chatbot...")
    
    try:
        from chatbot_simplified import get_chatbot_response, detect_user_intent, get_intent_actions
        print("✅ Simplified chatbot imported successfully")
        
        # Test various messages
        test_messages = [
            "Tell me about Melbourne Cricket Ground",
            "Help me book tickets",
            "What food is available?",
            "How do I park at the stadium?",
            "I need support"
        ]
        
        all_tests_passed = True
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n📤 Test {i}: '{message}'")
            
            try:
                response = get_chatbot_response(message)
                
                if response and 'response' in response:
                    print(f"✅ Response: {response['response'][:80]}...")
                    print(f"📊 Confidence: {response.get('confidence', 'N/A')}")
                    print(f"🔧 Model: {response.get('model', 'N/A')}")
                    
                    # Test intent detection
                    intent = detect_user_intent(message)
                    actions = get_intent_actions(intent)
                    print(f"🎯 Intent: {intent}")
                    print(f"⚡ Actions: {len(actions)} available")
                else:
                    print("❌ Invalid response format")
                    all_tests_passed = False
                    
            except Exception as e:
                print(f"❌ Test failed: {e}")
                all_tests_passed = False
        
        return all_tests_passed
        
    except Exception as e:
        print(f"❌ Chatbot test failed: {e}")
        return False

def test_flask_integration():
    """Test Flask integration"""
    print("\n🌐 Testing Flask Integration...")
    
    try:
        from app import app, CHATBOT_AVAILABLE
        
        if CHATBOT_AVAILABLE:
            print("✅ Chatbot available in Flask app")
            
            with app.app_context():
                print("✅ Flask app context working")
            
            return True
        else:
            print("❌ Chatbot not available in Flask app")
            return False
    except Exception as e:
        print(f"❌ Flask integration failed: {e}")
        return False

def main():
    """Run tests"""
    print("🏏 CricVerse AI Chatbot - Fixed Version Test")
    print("=" * 50)
    
    # Test Gemini API Key
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key and api_key.startswith('AIza'):
        print(f"✅ Gemini API Key: {api_key[:10]}...")
    else:
        print("❌ Gemini API Key not configured properly")
    
    # Run tests
    chatbot_test = test_simplified_chatbot()
    flask_test = test_flask_integration()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    print(f"Chatbot Tests:     {'✅ PASS' if chatbot_test else '❌ FAIL'}")
    print(f"Flask Integration: {'✅ PASS' if flask_test else '❌ FAIL'}")
    
    if chatbot_test and flask_test:
        print("\n🎉 All tests passed! Your AI chatbot is working correctly.")
        print("\n🚀 Next Steps:")
        print("1. Run your Flask app: python app.py")
        print("2. Visit http://localhost:5000/chat")
        print("3. Test the chatbot interface")
        print("4. Try the chatbot icon on any page")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
    
    return chatbot_test and flask_test

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)