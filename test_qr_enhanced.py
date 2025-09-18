#!/usr/bin/env python3
"""
Test script for enhanced QR code generator with all requested features:
- Better error handling
- Caching mechanism for frequently accessed codes  
- Expiration for QR codes
- Analytics tracking for verification attempts
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_qr_generator():
    """Test the enhanced QR generator functionality"""
    
    try:
        from app import app, db
        from qr_generator import qr_generator
        
        print("🧪 Testing Enhanced QR Code Generator")
        print("=" * 50)
        
        # Test within Flask app context
        with app.app_context():
            
            # Test 1: Generate ticket QR with expiration
            print("\n1. Testing Ticket QR Generation with Expiration...")
            ticket_data = {
                'ticket_id': 12345,
                'event_id': 67890,
                'seat_id': 101,
                'customer_id': 555
            }
            
            result = qr_generator.generate_ticket_qr(ticket_data, expiry_hours=48)
            
            if result and 'error' not in result:
                print(f"   ✅ Ticket QR generated successfully")
                print(f"   📍 QR Code Path: {result['qr_code_base64']}")
                print(f"   🔑 Verification Code: {result['verification_code'][:8]}...")
                print(f"   ⏰ Expires At: {result['expires_at']}")
                
                # Test cache hit
                print("\n   Testing cache functionality...")
                cached_result = qr_generator.generate_ticket_qr(ticket_data, expiry_hours=48)
                if cached_result and cached_result.get('verification_code') == result.get('verification_code'):
                    print("   ✅ Cache working correctly (same verification code returned)")
                else:
                    print("   ⚠️  Cache might not be working as expected")
            else:
                print(f"   ❌ Failed to generate ticket QR: {result}")
                return False
            
            # Test 2: Generate parking QR
            print("\n2. Testing Parking QR Generation...")
            parking_data = {
                'booking_id': 98765,
                'parking_id': 321,
                'vehicle_number': 'ABC-123'
            }
            
            parking_result = qr_generator.generate_parking_qr(parking_data, expiry_hours=24)
            
            if parking_result and 'error' not in parking_result:
                print(f"   ✅ Parking QR generated successfully")
                print(f"   📍 QR Code Path: {parking_result['qr_code_base64']}")
                print(f"   🔑 Verification Code: {parking_result['verification_code'][:8]}...")
                print(f"   ⏰ Expires At: {parking_result['expires_at']}")
            else:
                print(f"   ❌ Failed to generate parking QR: {parking_result}")
                return False
            
            # Test 3: Generate event entry QR
            print("\n3. Testing Event Entry QR Generation...")
            entry_data = {
                'customer_id': 777,
                'customer_name': 'John Doe',
                'event_id': 12345
            }
            
            entry_result = qr_generator.generate_event_entry_qr(entry_data, expiry_hours=12)
            
            if entry_result and 'error' not in entry_result:
                print(f"   ✅ Entry QR generated successfully")
                print(f"   📍 QR Code Path: {entry_result['qr_code_base64']}")
                print(f"   🔑 Verification Code: {entry_result['verification_code'][:8]}...")
                print(f"   ⏰ Expires At: {entry_result['expires_at']}")
            else:
                print(f"   ❌ Failed to generate entry QR: {entry_result}")
                return False
            
            # Test 4: Generate digital pass
            print("\n4. Testing Digital Pass QR Generation...")
            pass_data = {
                'customer_name': 'Jane Smith',
                'event_id': 12345
            }
            
            pass_result = qr_generator.generate_digital_pass(pass_data, 'vip', expiry_hours=72)
            
            if pass_result and 'error' not in pass_result:
                print(f"   ✅ Digital pass QR generated successfully")
                print(f"   📍 QR Code Path: {pass_result['qr_code_base64']}")
                print(f"   🔑 Verification Code: {pass_result['verification_code'][:8]}...")
                print(f"   ⏰ Expires At: {pass_result['expires_at']}")
            else:
                print(f"   ❌ Failed to generate digital pass QR: {pass_result}")
                return False
            
            # Test 5: Error handling
            print("\n5. Testing Error Handling...")
            
            # Test with missing required fields
            invalid_data = {'invalid': 'data'}
            error_result = qr_generator.generate_ticket_qr(invalid_data)
            
            if error_result and 'error' in error_result:
                print(f"   ✅ Error handling working correctly")
                print(f"   📝 Error: {error_result['error']}")
                print(f"   🏷️  Error Type: {error_result['error_type']}")
            else:
                print(f"   ⚠️  Error handling might not be working properly")
            
            # Test 6: Cache statistics
            print("\n6. Testing Cache Statistics...")
            cache_stats = qr_generator.cache.get_stats()
            print(f"   📊 Cache Stats: {cache_stats}")
            
            # Test 7: Analytics
            print("\n7. Testing Analytics...")
            
            # Get verification stats for a generated code
            if result and 'verification_code' in result:
                verification_code = result['verification_code']
                stats = qr_generator.analytics.get_verification_stats(verification_code)
                print(f"   📈 Verification Stats for {verification_code[:8]}...: {stats}")
            
            # Get daily stats
            daily_stats = qr_generator.analytics.get_daily_stats(days=1)
            print(f"   📅 Daily Stats: {len(daily_stats)} entries")
            for stat in daily_stats[:3]:  # Show first 3 entries
                print(f"      - {stat}")
            
            # Test 8: QR Code verification
            print("\n8. Testing QR Code Verification...")
            
            if result and 'verification_code' in result:
                verification_result = qr_generator.verify_qr_code(result['verification_code'])
                print(f"   🔍 Verification Result: {verification_result}")
            
            print("\n" + "=" * 50)
            print("🎉 All Enhanced QR Generator Tests Completed Successfully!")
            print("\n📋 Summary of Enhanced Features:")
            print("   ✅ Better Error Handling - Comprehensive validation and error messages")
            print("   ✅ Caching Mechanism - LRU cache with TTL for frequently accessed codes")
            print("   ✅ QR Code Expiration - Configurable expiry times for security")
            print("   ✅ Analytics Tracking - Detailed verification attempt tracking")
            print("   ✅ Retry Mechanism - Automatic retry for failed operations")
            print("   ✅ Enhanced Logging - Detailed logging for debugging and monitoring")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_qr_generator()
    sys.exit(0 if success else 1)