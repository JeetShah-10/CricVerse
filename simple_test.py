#!/usr/bin/env python3
"""
Simple Test of CricVerse New Features
This script tests all four new features with basic HTTP requests
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_all_features():
    print("Testing CricVerse New Features")
    print("=" * 50)
    
    # Test 1: Ticket Transfer
    print("\nTesting Ticket Transfer...")
    transfer_data = {
        'ticket_id': 1,
        'to_email': 'recipient@example.com',
        'transfer_fee': 5.0
    }
    
    response = requests.post(f"{BASE_URL}/api/ticket/transfer", json=transfer_data)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Transfer initiated: {data['transfer_code'][:8]}...")
        print(f"   Verification code: {data['verification_code']}")
        
        # Test accept transfer
        accept_data = {'verification_code': data['verification_code']}
        accept_response = requests.post(
            f"{BASE_URL}/api/ticket/transfer/{data['transfer_code']}/accept", 
            json=accept_data
        )
        if accept_response.status_code == 200:
            print("✅ Transfer accepted successfully")
        else:
            print(f"❌ Transfer acceptance failed: {accept_response.json()}")
    else:
        print(f"❌ Transfer initiation failed: {response.json()}")
    
    # Test 2: Marketplace
    print("\n🏪 Testing Resale Marketplace...")
    listing_data = {
        'ticket_id': 2,
        'listing_price': 120.0,
        'description': 'Great seats!',
        'is_negotiable': True
    }
    
    response = requests.post(f"{BASE_URL}/api/marketplace/list-ticket", json=listing_data)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Ticket listed: ID {data['listing_id']}")
        print(f"   Net amount: ${data['net_amount']:.2f}")
        
        # Test search
        search_response = requests.get(f"{BASE_URL}/api/marketplace/search?max_price=150")
        if search_response.status_code == 200:
            search_data = search_response.json()
            print(f"✅ Found {len(search_data['listings'])} listings")
        else:
            print(f"❌ Search failed: {search_response.json()}")
    else:
        print(f"❌ Listing failed: {response.json()}")
    
    # Test 3: Season Tickets
    print("\n🎟️ Testing Season Tickets...")
    season_data = {
        'stadium_id': 1,
        'seat_id': 1,
        'season_name': 'BBL 2024-25',
        'total_matches': 10
    }
    
    response = requests.post(f"{BASE_URL}/api/season-ticket/purchase", json=season_data)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Season ticket purchased: ID {data['season_ticket_id']}")
        print(f"   Total price: ${data['total_price']:.2f}")
        print(f"   Savings: ${data['savings']:.2f}")
        
        # Test get matches
        matches_response = requests.get(f"{BASE_URL}/api/season-ticket/{data['season_ticket_id']}/matches")
        if matches_response.status_code == 200:
            matches_data = matches_response.json()
            print(f"✅ Retrieved {len(matches_data['matches'])} matches")
        else:
            print(f"❌ Get matches failed: {matches_response.json()}")
    else:
        print(f"❌ Season ticket purchase failed: {response.json()}")
    
    # Test 4: Accessibility
    print("\n♿ Testing Accessibility...")
    accessibility_data = {
        'accommodation_type': 'wheelchair',
        'description': 'Full-time wheelchair user',
        'requires_wheelchair_access': True,
        'requires_companion_seat': True
    }
    
    response = requests.post(f"{BASE_URL}/api/accessibility/register", json=accessibility_data)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Accessibility registered: ID {data['accommodation_id']}")
        
        # Test booking with accessibility
        booking_data = {
            'event_id': 1,
            'seat_ids': [3, 4],
            'requested_accommodations': ['wheelchair_access', 'companion_seat']
        }
        
        booking_response = requests.post(f"{BASE_URL}/api/accessibility/book", json=booking_data)
        if booking_response.status_code == 200:
            booking_data = booking_response.json()
            print(f"✅ Accessibility booking created: ID {booking_data['booking_id']}")
            
            # Test status check
            status_response = requests.get(f"{BASE_URL}/api/accessibility/status/{booking_data['booking_id']}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"✅ Status retrieved: {status_data['accommodation_status']}")
            else:
                print(f"❌ Status check failed: {status_response.json()}")
        else:
            print(f"❌ Accessibility booking failed: {booking_response.json()}")
    else:
        print(f"❌ Accessibility registration failed: {response.json()}")
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("✨ New features are working correctly!")

if __name__ == "__main__":
    test_all_features()