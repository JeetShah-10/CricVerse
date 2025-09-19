"""
Supabase Integration for BBL Data
Example implementation for fetching live scores, standings, and team data from Supabase

Enhancements:
- Retry with exponential backoff around Supabase queries
- Schema fallback (plural vs singular tables): matches->event/match, teams->team, players->player
- Reduced payload selections and sensible limits to avoid timeouts
- Graceful degradation to mock data when schema differs or network issues occur
"""

import os
from typing import List, Dict, Optional, Any
import logging
import importlib
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BBLDataService:
    """Service class for fetching BBL data from Supabase"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        # Prefer anon key for REST; fallback to SUPABASE_KEY if provided
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_KEY')
        # Query hardening settings
        self.max_retries: int = int(os.getenv('SUPABASE_MAX_RETRIES', '3'))
        self.base_delay: float = float(os.getenv('SUPABASE_RETRY_BASE_DELAY', '0.35'))
        self.default_limit: int = int(os.getenv('SUPABASE_DEFAULT_LIMIT', '8'))
        
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

        # Cached basic schema capability checks to avoid repeated failing calls
        self._schema_cache: Dict[str, bool] = {}
        # Lightweight in-memory cache for common reads
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl: int = int(os.getenv('SUPABASE_CACHE_TTL', '20'))  # seconds

    # --------------- internal helpers ---------------
    def _with_retries(self, func, context: str):
        """Run a callable with retries and backoff. Return func() result or raise on final failure."""
        delay = self.base_delay
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                start = time.perf_counter()
                result = func()
                elapsed = (time.perf_counter() - start) * 1000.0
                logger.info(f"Supabase query ok ({context}) in {elapsed:.1f} ms")
                return result
            except Exception as e:
                last_exc = e
                if attempt >= self.max_retries:
                    break
                logger.warning(f"Supabase query failed ({context}) attempt {attempt}/{self.max_retries}: {e}. Retrying in {delay:.2f}s…")
                time.sleep(delay)
                delay *= 2
        # After retries exhausted
        raise last_exc if last_exc else RuntimeError(f"Unknown error in _with_retries for {context}")

    def _table_available(self, table_name: str) -> bool:
        """Check if a table is available by issuing a cheap probe and cache the result."""
        if not self.supabase:
            return False
        if table_name in self._schema_cache:
            return self._schema_cache[table_name]
        try:
            # Avoid HEAD requests (seen 401 on some setups). Use a small GET.
            def _probe():
                return self.supabase.table(table_name).select('id', count='exact').limit(1).execute()
            resp = self._with_retries(_probe, f"probe {table_name}")
            # If REST returns 401, treat as unavailable for this run (will fall back to mock)
            if hasattr(resp, 'status_code') and resp.status_code == 401:
                self._schema_cache[table_name] = False
                return False
            self._schema_cache[table_name] = True
            return True
        except Exception:
            self._schema_cache[table_name] = False
            return False

    def _cache_get(self, key: str):
        try:
            item = self._cache.get(key)
            if not item:
                return None
            if (time.time() - item['ts']) <= self.cache_ttl:
                return item['data']
        except Exception:
            pass
        return None

    def _cache_set(self, key: str, data: Any):
        try:
            self._cache[key] = {'data': data, 'ts': time.time()}
        except Exception:
            pass
    
    async def get_live_scores(self) -> List[Dict]:
        """Fetch live match scores and fixtures from Supabase"""
        if not self.supabase:
            return self._get_mock_live_scores()
        
        try:
            cached = self._cache_get('live_scores')
            if cached is not None:
                return cached
            matches: List[Dict] = []

            if self._table_available('matches'):
                def _q_matches():
                    return self.supabase.table('matches') \
                        .select('id, home_team_id, away_team_id, home_score, away_score, status, overs, venue, match_date') \
                        .in_('status', ['LIVE', 'UPCOMING']) \
                        .order('match_date') \
                        .limit(min(5, self.default_limit)) \
                        .execute()
                response = self._with_retries(_q_matches, 'matches list')
                # Optional: join team metadata if teams table exists
                team_meta: Dict[int, Dict] = {}
                if self._table_available('teams'):
                    # Fetch minimal team info in one go
                    team_ids = list({r.get('home_team_id') for r in response.data} | {r.get('away_team_id') for r in response.data})
                    team_ids = [tid for tid in team_ids if tid is not None]
                    if team_ids:
                        def _q_teams():
                            return self.supabase.table('teams') \
                                .select('id,name,logo_url') \
                                .in_('id', team_ids) \
                                .execute()
                        t_resp = self._with_retries(_q_teams, 'teams meta')
                        team_meta = {t['id']: t for t in (t_resp.data or [])}

                for match in response.data or []:
                    home = team_meta.get(match.get('home_team_id'), {})
                    away = team_meta.get(match.get('away_team_id'), {})
                    matches.append({
                        'id': match.get('id'),
                        'home_team': home.get('name') or f"Team {match.get('home_team_id')}",
                        'away_team': away.get('name') or f"Team {match.get('away_team_id')}",
                        'home_score': match.get('home_score'),
                        'away_score': match.get('away_score'),
                        'status': match.get('status') or 'UPCOMING',
                        'overs': match.get('overs'),
                        'venue': match.get('venue'),
                        'date': self._format_match_date(str(match.get('match_date'))),
                        'home_logo': home.get('logo_url'),
                        'away_logo': away.get('logo_url')
                    })
                self._cache_set('live_scores', matches)
                return matches

            # Fallback schema: use event + team tables (used across CricVerse UI)
            if self._table_available('event'):
                def _q_events():
                    return self.supabase.table('event') \
                        .select('id,home_team_id,away_team_id,event_date,start_time,match_status') \
                        .order('event_date') \
                        .order('start_time') \
                        .limit(min(6, self.default_limit)) \
                        .execute()
                ev_resp = self._with_retries(_q_events, 'events list')

                team_map: Dict[int, Dict] = {}
                if self._table_available('team'):
                    # Build unique ids set
                    ids = list({r.get('home_team_id') for r in ev_resp.data} | {r.get('away_team_id') for r in ev_resp.data})
                    ids = [i for i in ids if i is not None]
                    if ids:
                        def _q_team():
                            return self.supabase.table('team').select('id,team_name,team_logo').in_('id', ids).execute()
                        t_resp = self._with_retries(_q_team, 'team meta')
                        team_map = {t['id']: t for t in (t_resp.data or [])}

                for ev in ev_resp.data or []:
                    home = team_map.get(ev.get('home_team_id'), {})
                    away = team_map.get(ev.get('away_team_id'), {})
                    matches.append({
                        'id': ev.get('id'),
                        'home_team': home.get('team_name') or f"Team {ev.get('home_team_id')}",
                        'away_team': away.get('team_name') or f"Team {ev.get('away_team_id')}",
                        'home_score': None,
                        'away_score': None,
                        'status': (ev.get('match_status') or 'UPCOMING').upper(),
                        'overs': None,
                        'venue': None,
                        'date': self._format_match_date(str(ev.get('event_date'))),
                        'home_logo': home.get('team_logo'),
                        'away_logo': away.get('team_logo')
                    })
                self._cache_set('live_scores', matches)
                return matches

        except Exception as e:
            logger.error(f"Error fetching live scores: {e}")
            return self._get_mock_live_scores()
    
    async def get_standings(self) -> List[Dict]:
        """Fetch current BBL standings from Supabase"""
        if not self.supabase:
            return self._get_mock_standings()
        
        try:
            cached = self._cache_get('standings')
            if cached is not None:
                return cached
            standings: List[Dict] = []
            if self._table_available('teams'):
                def _q():
                    return self.supabase.table('teams') \
                        .select('id,name,logo_url,matches_played,matches_won,matches_lost,net_run_rate,points,is_playoff_eligible') \
                        .order('points', desc=True) \
                        .order('net_run_rate', desc=True) \
                        .limit(min(10, self.default_limit * 2)) \
                        .execute()
                response = self._with_retries(_q, 'standings teams')
                for i, team in enumerate(response.data or [], 1):
                    nrr = team.get('net_run_rate')
                    nrr_fmt = f"{nrr:+.2f}" if isinstance(nrr, (int, float)) else str(nrr) if nrr is not None else '+0.00'
                    standings.append({
                        'position': i,
                        'team': team.get('name'),
                        'played': team.get('matches_played'),
                        'won': team.get('matches_won'),
                        'lost': team.get('matches_lost'),
                        'nrr': nrr_fmt,
                        'points': team.get('points'),
                        'logo': team.get('logo_url'),
                        'is_playoff': team.get('is_playoff_eligible', False)
                    })
                self._cache_set('standings', standings)
                return standings

            # Fallback: If only generic team table exists, provide alphabetical ordering as pseudo-standings
            if self._table_available('team'):
                def _qt():
                    return self.supabase.table('team').select('id,team_name,team_logo').order('team_name').execute()
                resp = self._with_retries(_qt, 'team alphabetical')
                for i, t in enumerate(resp.data or [], 1):
                    standings.append({
                        'position': i,
                        'team': t.get('team_name'),
                        'played': None,
                        'won': None,
                        'lost': None,
                        'nrr': None,
                        'points': None,
                        'logo': t.get('team_logo'),
                        'is_playoff': False
                    })
                self._cache_set('standings', standings)
                return standings
            
        except Exception as e:
            logger.error(f"Error fetching standings: {e}")
            return self._get_mock_standings()
    
    async def get_top_performers(self) -> Dict[str, List[Dict]]:
        """Fetch top performing players from Supabase"""
        if not self.supabase:
            return self._get_mock_top_performers()
        
        try:
            cached = self._cache_get('top_performers')
            if cached is not None:
                return cached
            # Prefer rich players schema if present
            if self._table_available('players'):
                def _qr():
                    return self.supabase.table('players').select('id,name,team_id,total_runs,headshot_url').order('total_runs', desc=True).limit(4).execute()
                def _qw():
                    return self.supabase.table('players').select('id,name,team_id,total_wickets,headshot_url').order('total_wickets', desc=True).limit(4).execute()
                r = self._with_retries(_qr, 'players top runs')
                w = self._with_retries(_qw, 'players top wickets')

                team_meta: Dict[int, Dict] = {}
                team_ids = list({p.get('team_id') for p in (r.data or [])} | {p.get('team_id') for p in (w.data or [])})
                team_ids = [tid for tid in team_ids if tid is not None]
                if team_ids and self._table_available('teams'):
                    def _qt():
                        return self.supabase.table('teams').select('id,name,logo_url').in_('id', team_ids).execute()
                    t_resp = self._with_retries(_qt, 'teams for players')
                    team_meta = {t['id']: t for t in (t_resp.data or [])}

                top_runs = []
                for player in (r.data or []):
                    tm = team_meta.get(player.get('team_id'), {})
                    top_runs.append({
                        'id': player.get('id'),
                        'name': player.get('name'),
                        'team': tm.get('name'),
                        'runs': player.get('total_runs'),
                        'avatar': self._get_player_avatar(player.get('name', '')),
                        'logo': tm.get('logo_url'),
                        'headshot': player.get('headshot_url')
                    })

                top_wickets = []
                for player in (w.data or []):
                    tm = team_meta.get(player.get('team_id'), {})
                    top_wickets.append({
                        'id': player.get('id'),
                        'name': player.get('name'),
                        'team': tm.get('name'),
                        'wickets': player.get('total_wickets'),
                        'avatar': self._get_player_avatar(player.get('name', '')),
                        'logo': tm.get('logo_url'),
                        'headshot': player.get('headshot_url')
                    })

                result = { 'top_runs': top_runs, 'top_wickets': top_wickets }
                self._cache_set('top_performers', result)
                return result

            # Fallback: generic player table may have no stats; return mock in this case
            return self._get_mock_top_performers()
            
        except Exception as e:
            logger.error(f"Error fetching top performers: {e}")
            return self._get_mock_top_performers()
    
    async def get_teams(self) -> List[Dict]:
        """Fetch all BBL teams from Supabase"""
        if not self.supabase:
            return self._get_mock_teams()
        
        try:
            cached = self._cache_get('teams')
            if cached is not None:
                return cached
            teams: List[Dict] = []
            if self._table_available('teams'):
                def _q():
                    return self.supabase.table('teams').select('id,name,short_name,logo_url,primary_color,subtitle,points').order('points', desc=True).execute()
                resp = self._with_retries(_q, 'teams list')
                for i, team in enumerate(resp.data or [], 1):
                    teams.append({
                        'id': team.get('id'),
                        'name': team.get('name'),
                        'short_name': team.get('short_name'),
                        'position': i,
                        'points': team.get('points'),
                        'logo': team.get('logo_url'),
                        'color': team.get('primary_color'),
                        'subtitle': team.get('subtitle')
                    })
                self._cache_set('teams', teams)
                return teams

            if self._table_available('team'):
                def _qt():
                    return self.supabase.table('team').select('id,team_name,team_logo,team_color').order('team_name').execute()
                resp = self._with_retries(_qt, 'team list')
                for i, t in enumerate(resp.data or [], 1):
                    teams.append({
                        'id': t.get('id'),
                        'name': t.get('team_name'),
                        'short_name': None,
                        'position': i,
                        'points': None,
                        'logo': t.get('team_logo'),
                        'color': t.get('team_color'),
                        'subtitle': None
                    })
                self._cache_set('teams', teams)
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
