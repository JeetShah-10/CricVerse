#!/usr/bin/env python3
"""
Test script to verify PayPal and Razorpay credentials
"""

import os
from dotenv import load_dotenv
import paypalrestsdk

def load_environment():
    """Load environment variables from available .env files"""
    env_files = ['.env.corrected', '.env.final.merged', '.env.merged.complete', '.env.complete', '.env', '.env.development', 'cricverse.env']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"Loading environment from {env_file}")
            load_dotenv(env_file)
            return env_file
    
    print("No .env file found, using system environment variables")
    return None

def test_paypal_credentials():
    """Test PayPal credentials"""
    print("Testing PayPal credentials...")
    
    client_id = os.getenv('PAYPAL_CLIENT_ID')
    client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
    mode = os.getenv('PAYPAL_MODE', 'sandbox')
    
    # Check if credentials exist
    if not client_id:
        print("❌ PayPal Client ID not found")
        return False
        
    if not client_secret:
        print("❌ PayPal Client Secret not found")
        return False
    
    # Check if these are placeholder values
    if 'your_' in client_id.lower() or 'your_' in client_secret.lower() or '...' in client_id or '...' in client_secret:
        print("❌ PayPal credentials still contain placeholder values")
        print("   Please update PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in your .env file")
        return False
    
    try:
        # Configure PayPal SDK
        paypalrestsdk.configure({
            "mode": mode,
            "client_id": client_id,
            "client_secret": client_secret
        })
        
        # Test authentication by getting an access token
        token = paypalrestsdk.Api().get_access_token()
        if token:
            print("✅ PayPal credentials are valid!")
            return True
        else:
            print("❌ PayPal authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ PayPal test failed: {e}")
        print("   Please check your PayPal credentials and internet connection")
        return False

def test_razorpay_credentials():
    """Test Razorpay credentials"""
    print("\nTesting Razorpay credentials...")
    
    key_id = os.getenv('RAZORPAY_KEY_ID')
    key_secret = os.getenv('RAZORPAY_KEY_SECRET')
    
    # Check if credentials exist
    if not key_id:
        print("❌ Razorpay Key ID not found")
        return False
        
    if not key_secret:
        print("❌ Razorpay Key Secret not found")
        return False
    
    # Check if these are placeholder values
    if 'your_' in key_id.lower() or 'your_' in key_secret.lower() or '...' in key_id or '...' in key_secret:
        print("❌ Razorpay credentials still contain placeholder values")
        print("   Please update RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in your .env file")
        return False
    
    # For Razorpay, we'll just verify the credentials exist and format is correct
    if key_id.startswith('rzp_'):
        print("✅ Razorpay credentials format looks correct!")
        return True
    elif 'rzp_' in key_id:
        print("✅ Razorpay credentials format looks correct!")
        return True
    else:
        print("❌ Razorpay key ID format doesn't look correct")
        print("   Key ID should start with 'rzp_'")
        return False

def show_current_config():
    """Show current configuration values"""
    print("\nCurrent Configuration:")
    print("-" * 30)
    
    paypal_client_id = os.getenv('PAYPAL_CLIENT_ID', 'NOT SET')
    paypal_secret = os.getenv('PAYPAL_CLIENT_SECRET', 'NOT SET')
    razorpay_key_id = os.getenv('RAZORPAY_KEY_ID', 'NOT SET')
    razorpay_secret = os.getenv('RAZORPAY_KEY_SECRET', 'NOT SET')
    
    # Mask sensitive values for display
    if paypal_client_id != 'NOT SET':
        masked_paypal_id = paypal_client_id[:6] + "..." + paypal_client_id[-4:] if len(paypal_client_id) > 10 else "TOO SHORT"
    else:
        masked_paypal_id = 'NOT SET'
        
    if paypal_secret != 'NOT SET':
        masked_paypal_secret = "*" * min(len(paypal_secret), 20) + ("..." if len(paypal_secret) > 20 else "")
    else:
        masked_paypal_secret = 'NOT SET'
        
    if razorpay_key_id != 'NOT SET':
        masked_razorpay_id = razorpay_key_id[:6] + "..." + razorpay_key_id[-4:] if len(razorpay_key_id) > 10 else "TOO SHORT"
    else:
        masked_razorpay_id = 'NOT SET'
        
    if razorpay_secret != 'NOT SET':
        masked_razorpay_secret = "*" * min(len(razorpay_secret), 20) + ("..." if len(razorpay_secret) > 20 else "")
    else:
        masked_razorpay_secret = 'NOT SET'
    
    print(f"PayPal Client ID: {masked_paypal_id}")
    print(f"PayPal Secret:    {masked_paypal_secret}")
    print(f"Razorpay Key ID:  {masked_razorpay_id}")
    print(f"Razorpay Secret:  {masked_razorpay_secret}")

def main():
    """Main test function"""
    print("🔐 CricVerse Stadium System - Credential Tester")
    print("=" * 50)
    
    # Load environment variables
    loaded_env = load_environment()
    
    if loaded_env:
        print(f"✅ Loaded environment from: {loaded_env}")
    else:
        print("⚠️  No .env file found, using system environment variables")
    
    # Show current configuration
    show_current_config()
    
    # Test both payment systems
    paypal_ok = test_paypal_credentials()
    razorpay_ok = test_razorpay_credentials()
    
    print("\n" + "=" * 50)
    if paypal_ok and razorpay_ok:
        print("🎉 All credentials are properly configured!")
        print("🏆 Your CricVerse Stadium System is ready for Big Bash League fans worldwide!")
    elif paypal_ok:
        print("✅ PayPal is ready! (Razorpay needs configuration)")
        print("📝 Please add your Razorpay credentials to complete the setup")
    elif razorpay_ok:
        print("✅ Razorpay is ready! (PayPal configuration issue)")
    else:
        print("❌ Please check your credentials in the .env file")
    
    print("\n📝 Next steps:")
    print("1. If Razorpay shows placeholder values, add your actual Razorpay credentials")
    print("2. Run this test again to verify")
    print("3. Start your Flask app: python app.py")

if __name__ == "__main__":
    main()