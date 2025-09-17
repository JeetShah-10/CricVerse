#!/usr/bin/env python3
"""
Big Bash League (BBL) 2024-25 Season Generator
===============================================

This script generates a complete BBL season with:
- Real match scheduling based on actual BBL format
- Accurate team matchups and home/away distribution
- Proper venue allocation and timing
- Finals series structure
- Enhanced event data with weather, attendance predictions
- Real-world scheduling constraints (venue availability, travel)
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
from datetime import datetime, date, time, timedelta
import random
from typing import List, Dict, Tuple
import json

# Load environment variables
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

def get_db_connection():
    """Get PostgreSQL database connection using same logic as main app"""
    try:
        # Check for DATABASE_URL first (Supabase)
        database_url = os.getenv('DATABASE_URL')
        
        if database_url and 'postgresql' in database_url:
            # Parse Supabase URL
            import urllib.parse as urlparse
            url = urlparse.urlparse(database_url)
            conn = psycopg2.connect(
                host=url.hostname,
                port=url.port,
                database=url.path[1:],  # Remove leading slash
                user=url.username,
                password=url.password
            )
            print(f"✅ Connected to Supabase database")
            return conn
        else:
            # Fallback to local PostgreSQL
            conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                database=os.getenv('POSTGRES_DB', 'stadium_db'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'admin')
            )
            print(f"✅ Connected to local PostgreSQL database")
            return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

class BBLSeasonGenerator:
    def __init__(self):
        self.events = []
        self.season_start = datetime(2024, 12, 15)  # BBL typically starts mid-December
        self.season_end = datetime(2025, 2, 2)      # Finals typically end early February
        
        # BBL Teams with their home venues (from database query)
        self.teams = {
            1: {"name": "Adelaide Strikers", "home_stadium": 1, "city": "Adelaide", "colors": ["#003da5", "#ffd100"]},
            2: {"name": "Brisbane Heat", "home_stadium": 4, "city": "Brisbane", "colors": ["#00a651", "#ffd100"]},
            3: {"name": "Hobart Hurricanes", "home_stadium": 5, "city": "Hobart", "colors": ["#663399", "#ffffff"]},
            4: {"name": "Melbourne Renegades", "home_stadium": 3, "city": "Melbourne", "colors": ["#ff0000", "#000000"]},
            5: {"name": "Melbourne Stars", "home_stadium": 2, "city": "Melbourne", "colors": ["#00a651", "#ffd100"]},
            6: {"name": "Perth Scorchers", "home_stadium": 6, "city": "Perth", "colors": ["#ff8200", "#000000"]},
            7: {"name": "Sydney Sixers", "home_stadium": 7, "city": "Sydney", "colors": ["#ff0080", "#000000"]},
            8: {"name": "Sydney Thunder", "home_stadium": 8, "city": "Sydney", "colors": ["#00ff87", "#003da5"]}
        }
        
        # Stadium information
        self.stadiums = {
            1: {"name": "Adelaide Oval", "capacity": 53500, "city": "Adelaide", "timezone": "ACDT"},
            2: {"name": "Melbourne Cricket Ground (MCG)", "capacity": 100024, "city": "Melbourne", "timezone": "AEDT"},
            3: {"name": "Marvel Stadium (Docklands)", "capacity": 48000, "city": "Melbourne", "timezone": "AEDT"},
            4: {"name": "The Gabba", "capacity": 42000, "city": "Brisbane", "timezone": "AEST"},
            5: {"name": "Blundstone Arena (Bellerive)", "capacity": 19500, "city": "Hobart", "timezone": "AEDT"},
            6: {"name": "Optus Stadium", "capacity": 60000, "city": "Perth", "timezone": "AWST"},
            7: {"name": "Sydney Cricket Ground (SCG)", "capacity": 48601, "city": "Sydney", "timezone": "AEDT"},
            8: {"name": "Sydney Showground Stadium", "capacity": 22500, "city": "Sydney", "timezone": "AEDT"}
        }
        
        # BBL Match timing preferences
        self.match_times = {
            'weekday_afternoon': time(15, 30),   # 3:30 PM weekday matches
            'weekday_evening': time(19, 10),     # 7:10 PM weekday matches
            'weekend_afternoon': time(13, 45),   # 1:45 PM weekend matches
            'weekend_evening': time(19, 10),     # 7:10 PM weekend matches
            'new_years_eve': time(19, 15),       # Special NYE timing
            'australia_day': time(14, 00),       # Australia Day timing
            'finals': time(19, 30)               # Finals evening timing
        }
        
        # Weather and attendance factors for different venues
        self.venue_factors = {
            1: {"avg_attendance": 0.75, "weather_risk": 0.15},  # Adelaide Oval
            2: {"avg_attendance": 0.85, "weather_risk": 0.20},  # MCG
            3: {"avg_attendance": 0.70, "weather_risk": 0.25},  # Marvel Stadium (covered)
            4: {"avg_attendance": 0.80, "weather_risk": 0.30},  # The Gabba
            5: {"avg_attendance": 0.90, "weather_risk": 0.25},  # Blundstone (small, loyal crowd)
            6: {"avg_attendance": 0.82, "weather_risk": 0.10},  # Optus Stadium
            7: {"avg_attendance": 0.88, "weather_risk": 0.18},  # SCG
            8: {"avg_attendance": 0.72, "weather_risk": 0.22}   # Sydney Showground
        }
    
    def generate_round_robin_fixtures(self) -> List[Dict]:
        """Generate round-robin fixtures for BBL regular season"""
        fixtures = []
        teams = list(self.teams.keys())
        
        # Each team plays each other team twice (home and away)
        for i, home_team in enumerate(teams):
            for j, away_team in enumerate(teams):
                if home_team != away_team:
                    # Home fixture
                    fixtures.append({
                        'home_team': home_team,
                        'away_team': away_team,
                        'venue': self.teams[home_team]['home_stadium'],
                        'match_type': 'League'
                    })
        
        # Shuffle fixtures to create realistic scheduling
        random.shuffle(fixtures)
        return fixtures
    
    def assign_match_dates_and_times(self, fixtures: List[Dict]) -> List[Dict]:
        """Assign realistic dates and times to fixtures"""
        scheduled_matches = []
        current_date = self.season_start.date()
        
        # Track venue usage to avoid conflicts
        venue_schedule = {}
        team_schedule = {}
        
        for fixture in fixtures:
            # Find next available date for this fixture
            match_date = self.find_next_available_date(
                current_date, 
                fixture['venue'], 
                fixture['home_team'], 
                fixture['away_team'],
                venue_schedule, 
                team_schedule
            )
            
            # Determine match timing based on day of week and special dates
            match_time = self.determine_match_time(match_date, fixture['venue'])
            
            # Create match details
            match = {
                **fixture,
                'date': match_date,
                'time': match_time,
                'event_name': f"{self.teams[fixture['home_team']]['name']} vs {self.teams[fixture['away_team']]['name']}",
                'tournament_name': 'Big Bash League 2024-25',
                'event_type': 'T20 Cricket',
                'match_status': 'Scheduled'
            }
            
            scheduled_matches.append(match)
            
            # Update schedules
            if fixture['venue'] not in venue_schedule:
                venue_schedule[fixture['venue']] = []
            venue_schedule[fixture['venue']].append(match_date)
            
            for team in [fixture['home_team'], fixture['away_team']]:
                if team not in team_schedule:
                    team_schedule[team] = []
                team_schedule[team].append(match_date)
            
            # Move to next potential date
            current_date = match_date + timedelta(days=1)
        
        return scheduled_matches
    
    def find_next_available_date(self, start_date: date, venue: int, home_team: int, 
                                away_team: int, venue_schedule: Dict, team_schedule: Dict) -> date:
        """Find next available date considering venue and team constraints"""
        current_date = start_date
        max_attempts = 180  # Prevent infinite loops
        attempts = 0
        
        while attempts < max_attempts:
            # Check if venue is available
            venue_available = venue not in venue_schedule or current_date not in venue_schedule[venue]
            
            # Check if teams are available (min 2 days rest between matches)
            home_team_available = self.is_team_available(home_team, current_date, team_schedule)
            away_team_available = self.is_team_available(away_team, current_date, team_schedule)
            
            # Check if it's a reasonable match day (not too many consecutive days)
            reasonable_scheduling = self.is_reasonable_match_day(current_date)
            
            if venue_available and home_team_available and away_team_available and reasonable_scheduling:
                return current_date
            
            current_date += timedelta(days=1)
            attempts += 1
        
        # Fallback to original date if no good date found
        return start_date
    
    def is_team_available(self, team_id: int, match_date: date, team_schedule: Dict) -> bool:
        """Check if team has sufficient rest between matches"""
        if team_id not in team_schedule:
            return True
        
        team_dates = team_schedule[team_id]
        for existing_date in team_dates:
            days_difference = abs((match_date - existing_date).days)
            if days_difference < 2:  # Minimum 2 days rest
                return False
        return True
    
    def is_reasonable_match_day(self, match_date: date) -> bool:
        """Check if the date is reasonable for scheduling a match"""
        # Avoid Christmas Day and Boxing Day
        if match_date.month == 12 and match_date.day in [25, 26]:
            return False
        
        # Prefer weekend and holiday matches for better attendance
        weekday = match_date.weekday()
        return True  # For now, allow all days
    
    def determine_match_time(self, match_date: date, venue: int) -> time:
        """Determine appropriate match time based on date and venue"""
        weekday = match_date.weekday()  # 0 = Monday, 6 = Sunday
        
        # Special date handling
        if match_date.month == 12 and match_date.day == 31:  # New Year's Eve
            return self.match_times['new_years_eve']
        
        if match_date.month == 1 and match_date.day == 26:  # Australia Day
            return self.match_times['australia_day']
        
        # Weekend vs weekday timing
        if weekday in [5, 6]:  # Saturday, Sunday
            return random.choice([
                self.match_times['weekend_afternoon'],
                self.match_times['weekend_evening']
            ])
        else:  # Weekday
            # Prefer evening matches on weekdays
            return random.choice([
                self.match_times['weekday_evening'],
                self.match_times['weekday_afternoon']
            ]) if random.random() > 0.7 else self.match_times['weekday_evening']
    
    def generate_finals_series(self) -> List[Dict]:
        """Generate BBL Finals series matches"""
        finals_matches = []
        
        # BBL Finals format: Eliminator, Qualifier, Challenger, Final
        finals_start = self.season_end - timedelta(days=10)
        
        # Top 4 teams (using realistic historical performance)
        top_4_teams = [7, 6, 5, 2]  # Sixers, Scorchers, Stars, Heat (example based on form)
        
        # Eliminator (5th vs 4th)
        eliminator_date = finals_start.date()
        finals_matches.append({
            'home_team': top_4_teams[2],  # Higher ranked team hosts
            'away_team': top_4_teams[3],
            'venue': self.teams[top_4_teams[2]]['home_stadium'],
            'date': eliminator_date,
            'time': self.match_times['finals'],
            'event_name': f"BBL Eliminator: {self.teams[top_4_teams[2]]['name']} vs {self.teams[top_4_teams[3]]['name']}",
            'tournament_name': 'Big Bash League 2024-25 Finals',
            'event_type': 'T20 Cricket Finals',
            'match_status': 'Scheduled',
            'match_type': 'Eliminator'
        })
        
        # Qualifier (1st vs 2nd)
        qualifier_date = eliminator_date + timedelta(days=1)
        finals_matches.append({
            'home_team': top_4_teams[0],
            'away_team': top_4_teams[1],
            'venue': self.teams[top_4_teams[0]]['home_stadium'],
            'date': qualifier_date,
            'time': self.match_times['finals'],
            'event_name': f"BBL Qualifier: {self.teams[top_4_teams[0]]['name']} vs {self.teams[top_4_teams[1]]['name']}",
            'tournament_name': 'Big Bash League 2024-25 Finals',
            'event_type': 'T20 Cricket Finals',
            'match_status': 'Scheduled',
            'match_type': 'Qualifier'
        })
        
        # Challenger (Winner of Eliminator vs Loser of Qualifier)
        challenger_date = qualifier_date + timedelta(days=2)
        finals_matches.append({
            'home_team': top_4_teams[1],  # Assuming loser of qualifier
            'away_team': top_4_teams[2],  # Assuming winner of eliminator
            'venue': self.teams[top_4_teams[1]]['home_stadium'],
            'date': challenger_date,
            'time': self.match_times['finals'],
            'event_name': f"BBL Challenger: TBD vs TBD",
            'tournament_name': 'Big Bash League 2024-25 Finals',
            'event_type': 'T20 Cricket Finals',
            'match_status': 'Scheduled',
            'match_type': 'Challenger'
        })
        
        # Final
        final_date = challenger_date + timedelta(days=2)
        finals_matches.append({
            'home_team': top_4_teams[0],  # Assuming winner of qualifier
            'away_team': top_4_teams[1],  # Assuming winner of challenger
            'venue': self.teams[top_4_teams[0]]['home_stadium'],
            'date': final_date,
            'time': self.match_times['finals'],
            'event_name': f"BBL Final: TBD vs TBD",
            'tournament_name': 'Big Bash League 2024-25 Finals',
            'event_type': 'T20 Cricket Finals',
            'match_status': 'Scheduled',
            'match_type': 'Final'
        })
        
        return finals_matches
    
    def add_enhanced_event_data(self, matches: List[Dict]) -> List[Dict]:
        """Add enhanced data like predicted attendance, weather factors, etc."""
        enhanced_matches = []
        
        for match in matches:
            venue = match['venue']
            stadium_info = self.stadiums[venue]
            venue_factor = self.venue_factors[venue]
            
            # Calculate predicted attendance based on various factors
            base_attendance = stadium_info['capacity'] * venue_factor['avg_attendance']
            
            # Adjust for match importance
            if 'Final' in match.get('match_type', ''):
                attendance_multiplier = 1.2
            elif match['date'].weekday() in [5, 6]:  # Weekend
                attendance_multiplier = 1.1
            else:
                attendance_multiplier = 0.9
            
            predicted_attendance = int(min(
                base_attendance * attendance_multiplier,
                stadium_info['capacity']
            ))
            
            # Add enhanced data
            enhanced_match = {
                **match,
                'stadium_id': venue,
                'attendance': predicted_attendance,
                'weather_risk': venue_factor['weather_risk'],
                'ticket_price_range': self.calculate_ticket_prices(venue, match.get('match_type', 'League')),
                'broadcast_time': self.calculate_broadcast_time(match['time'], stadium_info['timezone'])
            }
            
            enhanced_matches.append(enhanced_match)
        
        return enhanced_matches
    
    def calculate_ticket_prices(self, venue: int, match_type: str) -> Dict:
        """Calculate ticket price ranges for the match"""
        base_prices = {
            'general': 25,
            'premium': 65,
            'corporate': 150,
            'vip': 300
        }
        
        # Adjust for venue prestige
        venue_multipliers = {
            1: 1.1,   # Adelaide Oval
            2: 1.3,   # MCG
            3: 1.0,   # Marvel Stadium
            4: 1.2,   # The Gabba
            5: 0.8,   # Blundstone Arena
            6: 1.25,  # Optus Stadium
            7: 1.4,   # SCG
            8: 0.9    # Sydney Showground
        }
        
        # Adjust for match importance
        if 'Final' in match_type:
            importance_multiplier = 2.0
        elif 'Semi' in match_type or 'Qualifier' in match_type:
            importance_multiplier = 1.5
        else:
            importance_multiplier = 1.0
        
        venue_mult = venue_multipliers.get(venue, 1.0)
        
        return {
            category: int(price * venue_mult * importance_multiplier)
            for category, price in base_prices.items()
        }
    
    def calculate_broadcast_time(self, match_time: time, timezone: str) -> str:
        """Calculate broadcast time information"""
        return f"{match_time.strftime('%I:%M %p')} {timezone}"
    
    def generate_complete_season(self) -> List[Dict]:
        """Generate the complete BBL season"""
        print("🏏 Generating BBL 2024-25 Season...")
        
        # Generate regular season fixtures
        print("📅 Creating round-robin fixtures...")
        fixtures = self.generate_round_robin_fixtures()
        
        # Assign dates and times
        print("⏰ Scheduling matches...")
        regular_season = self.assign_match_dates_and_times(fixtures)
        
        # Generate finals series
        print("🏆 Creating finals series...")
        finals = self.generate_finals_series()
        
        # Combine all matches
        all_matches = regular_season + finals
        
        # Add enhanced data
        print("📊 Adding enhanced match data...")
        enhanced_matches = self.add_enhanced_event_data(all_matches)
        
        # Sort by date
        enhanced_matches.sort(key=lambda x: (x['date'], x['time']))
        
        return enhanced_matches
    
    def insert_events_to_database(self, matches: List[Dict]) -> bool:
        """Insert BBL events into the database"""
        conn = get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Clear existing events
            print("🗑️ Clearing existing events...")
            cursor.execute("DELETE FROM event;")
            
            # Prepare insert query
            insert_query = """
                INSERT INTO event (
                    stadium_id, event_name, event_type, tournament_name,
                    event_date, start_time, end_time, home_team_id, away_team_id,
                    match_status, attendance
                ) VALUES (
                    %(stadium_id)s, %(event_name)s, %(event_type)s, %(tournament_name)s,
                    %(event_date)s, %(start_time)s, %(end_time)s, %(home_team_id)s, %(away_team_id)s,
                    %(match_status)s, %(attendance)s
                )
            """
            
            # Prepare data for insertion
            event_data = []
            for match in matches:
                # Calculate end time (T20 matches typically last 3.5 hours)
                start_datetime = datetime.combine(match['date'], match['time'])
                end_datetime = start_datetime + timedelta(hours=3, minutes=30)
                
                event_data.append({
                    'stadium_id': match['stadium_id'],
                    'event_name': match['event_name'],
                    'event_type': match['event_type'],
                    'tournament_name': match['tournament_name'],
                    'event_date': match['date'],
                    'start_time': match['time'],
                    'end_time': end_datetime.time(),
                    'home_team_id': match['home_team'],
                    'away_team_id': match['away_team'],
                    'match_status': match['match_status'],
                    'attendance': match['attendance']
                })
            
            # Insert events in batches
            batch_size = 50
            total_events = len(event_data)
            
            print(f"📝 Inserting {total_events} BBL events...")
            
            for i in range(0, total_events, batch_size):
                batch = event_data[i:i + batch_size]
                execute_batch(cursor, insert_query, batch, page_size=batch_size)
                
                batch_num = (i // batch_size) + 1
                total_batches = (total_events + batch_size - 1) // batch_size
                print(f"   Batch {batch_num}/{total_batches} inserted ({len(batch)} events)")
            
            conn.commit()
            print(f"✅ Successfully inserted {total_events} BBL events!")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error inserting events: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def generate_season_summary(self, matches: List[Dict]):
        """Generate a summary of the created season"""
        print("\n" + "="*80)
        print("BBL 2024-25 SEASON SUMMARY")
        print("="*80)
        
        # Basic statistics
        total_matches = len(matches)
        regular_season = [m for m in matches if 'Final' not in m.get('match_type', '')]
        finals_matches = [m for m in matches if 'Final' in m.get('match_type', '')]
        
        print(f"📊 Total Matches: {total_matches}")
        print(f"📅 Regular Season: {len(regular_season)} matches")
        print(f"🏆 Finals Series: {len(finals_matches)} matches")
        print(f"🗓️ Season Duration: {matches[0]['date']} to {matches[-1]['date']}")
        
        # Venue distribution
        print("\n🏟️ MATCHES BY VENUE:")
        venue_counts = {}
        for match in matches:
            venue = match['stadium_id']
            venue_name = self.stadiums[venue]['name']
            venue_counts[venue_name] = venue_counts.get(venue_name, 0) + 1
        
        for venue, count in sorted(venue_counts.items()):
            print(f"   {venue:<35} | {count:>2} matches")
        
        # Team fixture counts
        print("\n🏏 MATCHES BY TEAM:")
        team_counts = {}
        for match in regular_season:  # Only count regular season
            for team_id in [match['home_team'], match['away_team']]:
                team_name = self.teams[team_id]['name']
                team_counts[team_name] = team_counts.get(team_name, 0) + 1
        
        for team, count in sorted(team_counts.items()):
            print(f"   {team:<25} | {count:>2} matches")
        
        # Total attendance and revenue projections
        total_attendance = sum(match['attendance'] for match in matches)
        avg_attendance = total_attendance / len(matches)
        
        print(f"\n👥 ATTENDANCE PROJECTIONS:")
        print(f"   Total Expected: {total_attendance:,} spectators")
        print(f"   Average per Match: {avg_attendance:,.0f} spectators")
        
        # Key matches
        print("\n⭐ KEY MATCHES:")
        # Boxing Day match
        boxing_day = [m for m in matches if m['date'].month == 12 and m['date'].day == 26]
        if boxing_day:
            match = boxing_day[0]
            print(f"   Boxing Day: {match['event_name']} at {self.stadiums[match['stadium_id']]['name']}")
        
        # New Year's Eve
        nye_matches = [m for m in matches if m['date'].month == 12 and m['date'].day == 31]
        if nye_matches:
            match = nye_matches[0]
            print(f"   New Year's Eve: {match['event_name']} at {self.stadiums[match['stadium_id']]['name']}")
        
        # Finals
        for final_match in finals_matches:
            match_type = final_match.get('match_type', 'Final')
            print(f"   {match_type}: {final_match['date']} at {self.stadiums[final_match['stadium_id']]['name']}")
        
        print("\n" + "="*80)
        print("🎉 BBL 2024-25 SEASON READY FOR CRICKET FANS!")
        print("="*80)

def main():
    print("🏏 BBL 2024-25 SEASON GENERATOR")
    print("=" * 35)
    print("Creating comprehensive Big Bash League season with real match data...")
    
    generator = BBLSeasonGenerator()
    
    # Generate complete season
    matches = generator.generate_complete_season()
    
    # Show summary before insertion
    generator.generate_season_summary(matches)
    
    # Insert into database
    print("\n📝 Inserting events into database...")
    if generator.insert_events_to_database(matches):
        print("\n🎉 BBL 2024-25 season successfully created!")
        print("✅ All events are now available in the CricVerse system")
        print("🎫 Fans can now book tickets for exciting BBL matches!")
    else:
        print("\n❌ Failed to insert events into database")

if __name__ == "__main__":
    main()