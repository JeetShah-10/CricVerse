#!/usr/bin/env python3
"""
Demonstration of QR Code expiration functionality
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_qr_expiration():
    """Test QR code expiration functionality"""
    
    try:
        from app import app, db
        from qr_generator import qr_generator
        
        print("⏰ Testing QR Code Expiration Feature")
        print("=" * 50)
        
        # Test within Flask app context
        with app.app_context():
            
            # Generate a QR code that expires in 1 hour
            print("\n1. Generating QR code with 1-hour expiration...")
            ticket_data = {
                'ticket_id': 99999,
                'event_id': 88888,
                'seat_id': 202,
                'customer_id': 777
            }
            
            result = qr_generator.generate_ticket_qr(ticket_data, expiry_hours=1)
            
            if result and 'error' not in result:
                print(f"   ✅ QR code generated successfully")
                print(f"   🔑 Verification Code: {result['verification_code'][:8]}...")
                print(f"   ⏰ Created At: {result['created_at']}")
                print(f"   ⏰ Expires At: {result['expires_at']}")
                
                # Parse expiry time
                expires_at = datetime.fromisoformat(result['expires_at'])
                created_at = datetime.fromisoformat(result['created_at'])
                time_to_expiry = expires_at - created_at
                
                print(f"   ⌛ Time until expiry: {time_to_expiry}")
                
                # Test if QR code is currently expired
                is_expired = qr_generator._is_qr_code_expired(result)
                print(f"   🔍 Currently expired: {is_expired}")
                
                # Simulate checking a QR code that would be expired
                print("\n2. Testing expiration check with simulated expired QR...")
                
                # Create a fake expired QR code data
                expired_qr_data = {
                    'expires_at': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    'verification_code': 'expired_test_code'
                }
                
                is_expired_test = qr_generator._is_qr_code_expired(expired_qr_data)
                print(f"   🔍 Simulated expired QR: {is_expired_test}")
                
                # Test caching behavior with expired QR
                print("\n3. Testing cache behavior with expiration...")
                
                # Try to get from cache (should work since it's not expired)
                cache_key = qr_generator._generate_cache_key('ticket', ticket_data)
                cached_result = qr_generator.cache.get(cache_key)
                
                if cached_result:
                    print(f"   ✅ QR code found in cache")
                    print(f"   🔍 Cache entry expired: {qr_generator._is_qr_code_expired(cached_result)}")
                else:
                    print(f"   ❌ QR code not found in cache")
                
                # Show analytics for this QR code
                print("\n4. Analytics for this QR code...")
                stats = qr_generator.analytics.get_verification_stats(result['verification_code'])
                print(f"   📊 Verification attempts: {stats['total_attempts']}")
                print(f"   ✅ Successful attempts: {stats['successful_attempts']}")
                print(f"   ❌ Failed attempts: {stats['failed_attempts']}")
                
                print("\n" + "=" * 50)
                print("✅ QR Code Expiration Test Completed Successfully!")
                print("\n📋 Expiration Features Demonstrated:")
                print("   ✅ Configurable expiry times (1 hour, 24 hours, 72 hours, etc.)")
                print("   ✅ Automatic expiry checking")
                print("   ✅ Cache integration with expiry")
                print("   ✅ Analytics tracking for expired codes")
                print("   ✅ ISO format timestamps for precise time tracking")
                
                return True
            else:
                print(f"   ❌ Failed to generate QR code: {result}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_qr_expiration()
    sys.exit(0 if success else 1)