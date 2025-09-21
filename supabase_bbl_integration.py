"""
Supabase BBL Integration for CricVerse
Handles all BBL data operations with Supabase backend
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BBLDataService:
    """Service for fetching BBL data from Supabase"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("❌ Supabase credentials not found! Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
            raise ValueError("Supabase credentials are required")
        
        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info("✅ Supabase client initialized successfully")
            # Test connection
            self._test_connection()
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            raise ConnectionError(f"Cannot connect to Supabase: {e}")
    
    def _test_connection(self):
        """Test Supabase connection by querying a table"""
        try:
            response = self.supabase.table('team').select('id').limit(1).execute()
            logger.info("✅ Supabase connection test successful")
        except Exception as e:
            logger.error(f"❌ Supabase connection test failed: {e}")
            raise ConnectionError(f"Supabase connection test failed: {e}")
    
    async def get_live_scores(self) -> List[Dict[str, Any]]:
        """Get live BBL match scores from Supabase"""
        try:
            # Query live matches from Supabase
            response = self.supabase.table('matches').select(
                'id, home_team_id, away_team_id, match_date, status, home_score, away_score, venue'
            ).eq('status', 'live').execute()
            
            matches = []
            for match in response.data:
                # Get team names
                home_team = await self._get_team_name(match['home_team_id'])
                away_team = await self._get_team_name(match['away_team_id'])
                
                matches.append({
                    'id': match['id'],
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_score': match.get('home_score', '0/0'),
                    'away_score': match.get('away_score', '0/0'),
                    'status': match['status'],
                    'venue': match.get('venue', 'TBD'),
                    'match_date': match['match_date']
                })
            
            logger.info(f"✅ Retrieved {len(matches)} live matches from Supabase")
            return matches
            
        except Exception as e:
            logger.error(f"❌ Error fetching live scores from Supabase: {e}")
            raise
    
    async def get_standings(self) -> List[Dict[str, Any]]:
        """Get BBL team standings from Supabase"""
        try:
            response = self.supabase.table('team_standings').select(
                'team_id, team_name, matches_played, wins, losses, points, net_run_rate'
            ).order('points', desc=True).execute()
            
            logger.info(f"✅ Retrieved {len(response.data)} team standings from Supabase")
            return response.data
            
        except Exception as e:
            logger.error(f"❌ Error fetching standings from Supabase: {e}")
            raise
    
    async def get_teams(self) -> List[Dict[str, Any]]:
        """Get all BBL teams from Supabase"""
        try:
            response = self.supabase.table('team').select(
                'id, team_name, team_logo, team_color, home_ground'
            ).order('team_name').execute()
            
            logger.info(f"✅ Retrieved {len(response.data)} teams from Supabase")
            return response.data
            
        except Exception as e:
            logger.error(f"❌ Error fetching teams from Supabase: {e}")
            raise
    
    async def get_top_performers(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get top performers (runs and wickets) from Supabase"""
        try:
            # Get top run scorers
            runs_response = self.supabase.table('player_stats').select(
                'player_id, player_name, team_name, runs, matches'
            ).order('runs', desc=True).limit(10).execute()
            
            # Get top wicket takers
            wickets_response = self.supabase.table('player_stats').select(
                'player_id, player_name, team_name, wickets, matches'
            ).order('wickets', desc=True).limit(10).execute()
            
            result = {
                'top_runs': runs_response.data,
                'top_wickets': wickets_response.data
            }
            
            logger.info(f"✅ Retrieved top performers from Supabase: {len(runs_response.data)} run scorers, {len(wickets_response.data)} wicket takers")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error fetching top performers from Supabase: {e}")
            raise
    
    async def _get_team_name(self, team_id: int) -> str:
        """Get team name by ID from Supabase"""
        try:
            response = self.supabase.table('team').select('team_name').eq('id', team_id).execute()
            if response.data:
                return response.data[0]['team_name']
            else:
                logger.warning(f"⚠️ Team with ID {team_id} not found in Supabase")
                return f"Unknown Team (ID: {team_id})"
        except Exception as e:
            logger.error(f"❌ Error fetching team name for ID {team_id}: {e}")
            raise

# Global instance - will be initialized when Supabase credentials are available
try:
    bbl_data_service = BBLDataService()
    logger.info("✅ BBL Data Service initialized successfully")
except (ValueError, ConnectionError) as e:
    logger.error(f"❌ BBL Data Service initialization failed: {e}")
    bbl_data_service = None
