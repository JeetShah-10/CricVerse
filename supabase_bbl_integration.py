"""
Supabase Integration for BBL Data
Example implementation for fetching live scores, standings, and team data from Supabase
"""

import os
from typing import List, Dict, Optional, Any
import logging
import importlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BBLDataService:
    """Service class for fetching BBL data from Supabase"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not found. Using mock data.")
            self.supabase = None
        else:
            # Lazy import supabase to avoid local module name collisions (e.g., realtime.py)
            try:
                supabase_mod = importlib.import_module('supabase')
                create_client = getattr(supabase_mod, 'create_client')
                self.supabase: Any = create_client(self.supabase_url, self.supabase_key)
            except Exception as e:
                logger.warning(f"Supabase client import/init failed, falling back to mock: {e}")
                self.supabase = None
    
    async def get_live_scores(self) -> List[Dict]:
        """Fetch live match scores and fixtures from Supabase"""
        if not self.supabase:
            return self._get_mock_live_scores()
        
        try:
            # Query matches table with team information
            response = self.supabase.table('matches')\
                .select('''
                    id,
                    home_team_id,
                    away_team_id,
                    home_score,
                    away_score,
                    status,
                    overs,
                    venue,
                    match_date,
                    teams_home:home_team_id(name, logo_url),
                    teams_away:away_team_id(name, logo_url)
                ''')\
                .in_('status', ['LIVE', 'UPCOMING'])\
                .order('match_date')\
                .limit(5)\
                .execute()
            
            matches = []
            for match in response.data:
                matches.append({
                    'id': match['id'],
                    'home_team': match['teams_home']['name'],
                    'away_team': match['teams_away']['name'],
                    'home_score': match['home_score'],
                    'away_score': match['away_score'],
                    'status': match['status'],
                    'overs': match['overs'],
                    'venue': match['venue'],
                    'date': self._format_match_date(match['match_date']),
                    'home_logo': match['teams_home']['logo_url'],
                    'away_logo': match['teams_away']['logo_url']
                })
            
            return matches
            
        except Exception as e:
            logger.error(f"Error fetching live scores: {e}")
            return self._get_mock_live_scores()
    
    async def get_standings(self) -> List[Dict]:
        """Fetch current BBL standings from Supabase"""
        if not self.supabase:
            return self._get_mock_standings()
        
        try:
            # Query teams table with calculated standings
            response = self.supabase.table('teams')\
                .select('''
                    id,
                    name,
                    logo_url,
                    matches_played,
                    matches_won,
                    matches_lost,
                    net_run_rate,
                    points,
                    is_playoff_eligible
                ''')\
                .order('points', desc=True)\
                .order('net_run_rate', desc=True)\
                .execute()
            
            standings = []
            for i, team in enumerate(response.data, 1):
                standings.append({
                    'position': i,
                    'team': team['name'],
                    'played': team['matches_played'],
                    'won': team['matches_won'],
                    'lost': team['matches_lost'],
                    'nrr': f"{team['net_run_rate']:+.2f}",
                    'points': team['points'],
                    'logo': team['logo_url'],
                    'is_playoff': team['is_playoff_eligible']
                })
            
            return standings
            
        except Exception as e:
            logger.error(f"Error fetching standings: {e}")
            return self._get_mock_standings()
    
    async def get_top_performers(self) -> Dict[str, List[Dict]]:
        """Fetch top performing players from Supabase"""
        if not self.supabase:
            return self._get_mock_top_performers()
        
        try:
            # Query players table for top run scorers
            top_runs_response = self.supabase.table('players')\
                .select('''
                    id,
                    name,
                    team_id,
                    total_runs,
                    headshot_url,
                    teams(name, logo_url)
                ''')\
                .order('total_runs', desc=True)\
                .limit(4)\
                .execute()
            
            # Query players table for top wicket takers
            top_wickets_response = self.supabase.table('players')\
                .select('''
                    id,
                    name,
                    team_id,
                    total_wickets,
                    headshot_url,
                    teams(name, logo_url)
                ''')\
                .order('total_wickets', desc=True)\
                .limit(4)\
                .execute()
            
            top_runs = []
            for player in top_runs_response.data:
                top_runs.append({
                    'id': player['id'],
                    'name': player['name'],
                    'team': player['teams']['name'],
                    'runs': player['total_runs'],
                    'avatar': self._get_player_avatar(player['name']),
                    'logo': player['teams']['logo_url'],
                    'headshot': player['headshot_url']
                })
            
            top_wickets = []
            for player in top_wickets_response.data:
                top_wickets.append({
                    'id': player['id'],
                    'name': player['name'],
                    'team': player['teams']['name'],
                    'wickets': player['total_wickets'],
                    'avatar': self._get_player_avatar(player['name']),
                    'logo': player['teams']['logo_url'],
                    'headshot': player['headshot_url']
                })
            
            return {
                'top_runs': top_runs,
                'top_wickets': top_wickets
            }
            
        except Exception as e:
            logger.error(f"Error fetching top performers: {e}")
            return self._get_mock_top_performers()
    
    async def get_teams(self) -> List[Dict]:
        """Fetch all BBL teams from Supabase"""
        if not self.supabase:
            return self._get_mock_teams()
        
        try:
            response = self.supabase.table('teams')\
                .select('''
                    id,
                    name,
                    short_name,
                    logo_url,
                    primary_color,
                    subtitle,
                    points,
                    matches_played
                ''')\
                .order('points', desc=True)\
                .execute()
            
            teams = []
            for i, team in enumerate(response.data, 1):
                teams.append({
                    'id': team['id'],
                    'name': team['name'],
                    'short_name': team['short_name'],
                    'position': i,
                    'points': team['points'],
                    'logo': team['logo_url'],
                    'color': team['primary_color'],
                    'subtitle': team['subtitle']
                })
            
            return teams
            
        except Exception as e:
            logger.error(f"Error fetching teams: {e}")
            return self._get_mock_teams()
    
    def _format_match_date(self, match_date: str) -> str:
        """Format match date for display"""
        from datetime import datetime, timedelta
        
        try:
            match_dt = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
            now = datetime.now()
            
            if match_dt.date() == now.date():
                return f"Today, {match_dt.strftime('%I:%M %p')}"
            elif match_dt.date() == (now + timedelta(days=1)).date():
                return f"Tomorrow, {match_dt.strftime('%I:%M %p')}"
            else:
                return match_dt.strftime('%b %d, %I:%M %p')
        except:
            return match_date
    
    def _get_player_avatar(self, name: str) -> str:
        """Generate player avatar initials"""
        names = name.split()
        if len(names) >= 2:
            return f"{names[0][0]}{names[1][0]}".upper()
        return name[:2].upper()
    
    # Mock data methods for when Supabase is not available
    def _get_mock_live_scores(self) -> List[Dict]:
        """Return mock live scores data"""
        return [
            {
                'id': 1,
                'home_team': 'Melbourne Stars',
                'away_team': 'Sydney Sixers',
                'home_score': '156/4',
                'away_score': '132/6',
                'status': 'LIVE',
                'overs': '15.3',
                'venue': 'Melbourne Cricket Ground',
                'date': 'Today, 7:15 PM',
                'home_logo': '/static/img/teams/Melbourne_Stars_logo.png',
                'away_logo': '/static/img/teams/Sydney_Sixers_logo.svg.png'
            }
        ]
    
    def _get_mock_standings(self) -> List[Dict]:
        """Return mock standings data"""
        return [
            {
                'position': 1,
                'team': 'Melbourne Stars',
                'played': 8,
                'won': 6,
                'lost': 2,
                'nrr': '+0.85',
                'points': 16,
                'logo': '/static/img/teams/Melbourne_Stars_logo.png',
                'is_playoff': True
            }
        ]
    
    def _get_mock_top_performers(self) -> Dict[str, List[Dict]]:
        """Return mock top performers data"""
        return {
            'top_runs': [
                {
                    'id': 1,
                    'name': 'Marcus Stoinis',
                    'team': 'Melbourne Stars',
                    'runs': 485,
                    'avatar': 'MS',
                    'logo': '/static/img/teams/Melbourne_Stars_logo.png',
                    'headshot': '/static/img/players/marcus_stoinis.jpg'
                }
            ],
            'top_wickets': [
                {
                    'id': 1,
                    'name': 'Trent Boult',
                    'team': 'Hobart Hurricanes',
                    'wickets': 24,
                    'avatar': 'TB',
                    'logo': '/static/img/teams/Hobart Hurricanes.png',
                    'headshot': '/static/img/players/trent_boult.jpg'
                }
            ]
        }
    
    def _get_mock_teams(self) -> List[Dict]:
        """Return mock teams data"""
        return [
            {
                'id': 1,
                'name': 'Melbourne Stars',
                'short_name': 'STA',
                'position': 1,
                'points': 16,
                'logo': '/static/img/teams/Melbourne_Stars_logo.png',
                'color': '#00A651',
                'subtitle': 'Shine Bright'
            }
        ]


# Example usage in Flask routes
async def get_live_scores_from_supabase():
    """Example function to use in Flask routes"""
    bbl_service = BBLDataService()
    return await bbl_service.get_live_scores()

async def get_standings_from_supabase():
    """Example function to use in Flask routes"""
    bbl_service = BBLDataService()
    return await bbl_service.get_standings()

async def get_top_performers_from_supabase():
    """Example function to use in Flask routes"""
    bbl_service = BBLDataService()
    return await bbl_service.get_top_performers()

async def get_teams_from_supabase():
    """Example function to use in Flask routes"""
    bbl_service = BBLDataService()
    return await bbl_service.get_teams()


# Database schema examples for Supabase
SUPABASE_SCHEMA_EXAMPLES = """
-- Teams table
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(10) NOT NULL,
    logo_url TEXT,
    primary_color VARCHAR(7),
    subtitle VARCHAR(100),
    matches_played INTEGER DEFAULT 0,
    matches_won INTEGER DEFAULT 0,
    matches_lost INTEGER DEFAULT 0,
    net_run_rate DECIMAL(5,2) DEFAULT 0.00,
    points INTEGER DEFAULT 0,
    is_playoff_eligible BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Players table
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    team_id INTEGER REFERENCES teams(id),
    total_runs INTEGER DEFAULT 0,
    total_wickets INTEGER DEFAULT 0,
    headshot_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Matches table
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    home_score VARCHAR(20),
    away_score VARCHAR(20),
    status VARCHAR(20) DEFAULT 'UPCOMING',
    overs VARCHAR(10),
    venue VARCHAR(200),
    match_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sample data insertion
INSERT INTO teams (name, short_name, logo_url, primary_color, subtitle) VALUES
('Melbourne Stars', 'STA', '/static/img/teams/Melbourne_Stars_logo.png', '#00A651', 'Shine Bright'),
('Sydney Sixers', 'SIX', '/static/img/teams/Sydney_Sixers_logo.svg.png', '#FF1493', 'Six Appeal'),
('Perth Scorchers', 'SCO', '/static/img/teams/Perth Scorchers.png', '#FF8800', 'Desert Fire'),
('Brisbane Heat', 'HEA', '/static/img/teams/Brisbane Heat.png', '#FF6B35', 'Feel the Heat'),
('Hobart Hurricanes', 'HUR', '/static/img/teams/Hobart Hurricanes.png', '#6B2C91', 'Hurricane Force'),
('Adelaide Strikers', 'STR', '/static/img/teams/Adelaide Striker.png', '#003DA5', 'The Strike Force'),
('Melbourne Renegades', 'REN', '/static/img/teams/Melbourne Renegades.png', '#E40613', 'Rebel Spirit'),
('Sydney Thunder', 'THU', '/static/img/teams/Sydney Thunder.png', '#FFED00', 'Thunder Strike');
"""

if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def main():
        bbl_service = BBLDataService()
        
        print("Fetching live scores...")
        live_scores = await bbl_service.get_live_scores()
        print(f"Found {len(live_scores)} matches")
        
        print("Fetching standings...")
        standings = await bbl_service.get_standings()
        print(f"Found {len(standings)} teams")
        
        print("Fetching top performers...")
        performers = await bbl_service.get_top_performers()
        print(f"Found {len(performers['top_runs'])} top run scorers")
        print(f"Found {len(performers['top_wickets'])} top wicket takers")
        
        print("Fetching teams...")
        teams = await bbl_service.get_teams()
        print(f"Found {len(teams)} teams")
    
    asyncio.run(main())
