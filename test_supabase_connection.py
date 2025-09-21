#!/usr/bin/env python3
"""
Comprehensive Supabase Connection Test for CricVerse
Tests all BBL data endpoints and Supabase integration
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase_bbl_integration import BBLDataService
from supabase_config import SupabaseConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SupabaseConnectionTester:
    """Comprehensive Supabase connection and data testing"""
    
    def __init__(self):
        self.config = SupabaseConfig()
        self.bbl_service = None
        self.test_results = {
            'config_validation': False,
            'connection_test': False,
            'bbl_service_init': False,
            'live_scores': False,
            'standings': False,
            'teams': False,
            'top_performers': False,
            'team_lookup': False
        }
    
    def run_all_tests(self):
        """Run comprehensive Supabase tests"""
        print("=" * 80)
        print("CRICVERSE SUPABASE CONNECTION TEST")
        print("=" * 80)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test 1: Configuration Validation
        self.test_config_validation()
        
        # Test 2: Basic Connection
        self.test_connection()
        
        # Test 3: BBL Service Initialization
        self.test_bbl_service_init()
        
        if self.bbl_service:
            # Test 4: Data Retrieval Tests
            asyncio.run(self.test_data_retrieval())
        
        # Test 5: Generate Summary
        self.generate_test_summary()
    
    def test_config_validation(self):
        """Test Supabase configuration validation"""
        print("1. Testing Supabase Configuration...")
        print("-" * 40)
        
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            
            print(f"SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
            print(f"SUPABASE_ANON_KEY: {'✅ Set' if supabase_key else '❌ Missing'}")
            
            if supabase_url:
                print(f"URL: {supabase_url[:50]}...")
            
            if supabase_key:
                print(f"Key: {supabase_key[:20]}...")
            
            is_valid = self.config.validate_config()
            self.test_results['config_validation'] = is_valid
            
            print(f"Configuration Status: {'✅ Valid' if is_valid else '❌ Invalid'}")
            
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")
            self.test_results['config_validation'] = False
        
        print()
    
    def test_connection(self):
        """Test basic Supabase connection"""
        print("2. Testing Supabase Connection...")
        print("-" * 40)
        
        try:
            if not self.test_results['config_validation']:
                print("❌ Skipping connection test - invalid configuration")
                return
            
            connection_ok = self.config.test_connection()
            self.test_results['connection_test'] = connection_ok
            
            print(f"Connection Status: {'✅ Connected' if connection_ok else '❌ Failed'}")
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            self.test_results['connection_test'] = False
        
        print()
    
    def test_bbl_service_init(self):
        """Test BBL service initialization"""
        print("3. Testing BBL Service Initialization...")
        print("-" * 40)
        
        try:
            if not self.test_results['connection_test']:
                print("❌ Skipping BBL service test - connection failed")
                return
            
            self.bbl_service = BBLDataService()
            self.test_results['bbl_service_init'] = True
            print("✅ BBL Service initialized successfully")
            
        except Exception as e:
            print(f"❌ BBL Service initialization failed: {e}")
            self.test_results['bbl_service_init'] = False
        
        print()
    
    async def test_data_retrieval(self):
        """Test all BBL data retrieval methods"""
        print("4. Testing BBL Data Retrieval...")
        print("-" * 40)
        
        # Test Live Scores
        await self.test_live_scores()
        
        # Test Standings
        await self.test_standings()
        
        # Test Teams
        await self.test_teams()
        
        # Test Top Performers
        await self.test_top_performers()
        
        # Test Team Lookup
        await self.test_team_lookup()
    
    async def test_live_scores(self):
        """Test live scores retrieval"""
        try:
            print("  Testing Live Scores...")
            scores = await self.bbl_service.get_live_scores()
            self.test_results['live_scores'] = True
            print(f"  ✅ Live Scores: Retrieved {len(scores)} matches")
            
            if scores:
                sample = scores[0]
                print(f"     Sample: {sample.get('home_team', 'N/A')} vs {sample.get('away_team', 'N/A')}")
            
        except Exception as e:
            print(f"  ❌ Live Scores failed: {e}")
            self.test_results['live_scores'] = False
    
    async def test_standings(self):
        """Test standings retrieval"""
        try:
            print("  Testing Standings...")
            standings = await self.bbl_service.get_standings()
            self.test_results['standings'] = True
            print(f"  ✅ Standings: Retrieved {len(standings)} teams")
            
            if standings:
                sample = standings[0]
                print(f"     Top Team: {sample.get('team_name', 'N/A')} ({sample.get('points', 0)} points)")
            
        except Exception as e:
            print(f"  ❌ Standings failed: {e}")
            self.test_results['standings'] = False
    
    async def test_teams(self):
        """Test teams retrieval"""
        try:
            print("  Testing Teams...")
            teams = await self.bbl_service.get_teams()
            self.test_results['teams'] = True
            print(f"  ✅ Teams: Retrieved {len(teams)} teams")
            
            if teams:
                sample = teams[0]
                print(f"     Sample: {sample.get('team_name', 'N/A')} - {sample.get('home_ground', 'N/A')}")
            
        except Exception as e:
            print(f"  ❌ Teams failed: {e}")
            self.test_results['teams'] = False
    
    async def test_top_performers(self):
        """Test top performers retrieval"""
        try:
            print("  Testing Top Performers...")
            performers = await self.bbl_service.get_top_performers()
            self.test_results['top_performers'] = True
            
            runs_count = len(performers.get('top_runs', []))
            wickets_count = len(performers.get('top_wickets', []))
            
            print(f"  ✅ Top Performers: {runs_count} run scorers, {wickets_count} wicket takers")
            
            if performers.get('top_runs'):
                top_scorer = performers['top_runs'][0]
                print(f"     Top Scorer: {top_scorer.get('player_name', 'N/A')} ({top_scorer.get('runs', 0)} runs)")
            
        except Exception as e:
            print(f"  ❌ Top Performers failed: {e}")
            self.test_results['top_performers'] = False
    
    async def test_team_lookup(self):
        """Test team name lookup"""
        try:
            print("  Testing Team Lookup...")
            team_name = await self.bbl_service._get_team_name(1)
            self.test_results['team_lookup'] = True
            print(f"  ✅ Team Lookup: Team ID 1 = {team_name}")
            
        except Exception as e:
            print(f"  ❌ Team Lookup failed: {e}")
            self.test_results['team_lookup'] = False
        
        print()
    
    def generate_test_summary(self):
        """Generate comprehensive test summary"""
        print("5. Test Summary")
        print("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        print("Detailed Results:")
        print("-" * 40)
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print()
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: Supabase integration is working perfectly!")
        elif success_rate >= 70:
            print("✅ GOOD: Supabase integration is mostly working")
        elif success_rate >= 50:
            print("⚠️ PARTIAL: Some Supabase features are working")
        else:
            print("❌ CRITICAL: Supabase integration has major issues")
        
        print()
        
        if not self.test_results['config_validation']:
            print("🔧 NEXT STEPS:")
            print("1. Set SUPABASE_URL in your environment")
            print("2. Set SUPABASE_ANON_KEY in your environment")
            print("3. Ensure your Supabase project is active")
        elif not self.test_results['connection_test']:
            print("🔧 NEXT STEPS:")
            print("1. Check your Supabase project URL")
            print("2. Verify your API key is correct")
            print("3. Ensure your Supabase project is not paused")
        elif passed_tests < total_tests:
            print("🔧 NEXT STEPS:")
            print("1. Check your Supabase database schema")
            print("2. Ensure required tables exist (team, matches, etc.)")
            print("3. Verify table permissions in Supabase")
        
        print("=" * 80)
        return success_rate >= 70

def main():
    """Main test execution"""
    try:
        tester = SupabaseConnectionTester()
        success = tester.run_all_tests()
        
        if success:
            print("✅ All tests completed successfully!")
            sys.exit(0)
        else:
            print("❌ Some tests failed. Check the output above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
