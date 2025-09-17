#!/usr/bin/env python3
"""
BBL Events Verification Script
Verifies that all BBL events were correctly inserted into the database
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv('cricverse.env')

def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    if database_url and 'postgresql' in database_url:
        import urllib.parse as urlparse
        url = urlparse.urlparse(database_url)
        return psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],
            user=url.username,
            password=url.password
        )

def main():
    conn = get_db_connection()
    cursor = conn.cursor()

    print('🏆 FINALS SERIES MATCHES:')
    cursor.execute('''
        SELECT e.event_name, e.event_date, e.start_time, s.name, e.attendance
        FROM event e
        JOIN stadium s ON e.stadium_id = s.id
        WHERE e.tournament_name LIKE '%Finals%'
        ORDER BY e.event_date, e.start_time;
    ''')
    finals = cursor.fetchall()
    for final in finals:
        print(f'   {final[1]} {final[2]} - {final[0]}')
        print(f'     🏟️ {final[3]} | 👥 {final[4]:,} expected')

    print('\n⭐ SPECIAL DATE MATCHES:')
    # Boxing Day matches
    cursor.execute('''
        SELECT e.event_name, e.event_date, e.start_time, s.name
        FROM event e
        JOIN stadium s ON e.stadium_id = s.id
        WHERE EXTRACT(month FROM e.event_date) = 12 AND EXTRACT(day FROM e.event_date) = 26
        ORDER BY e.start_time;
    ''')
    boxing_day = cursor.fetchall()
    if boxing_day:
        print('   Boxing Day:')
        for match in boxing_day:
            print(f'     {match[1]} {match[2]} - {match[0]} at {match[3]}')

    # New Year's Eve matches
    cursor.execute('''
        SELECT e.event_name, e.event_date, e.start_time, s.name
        FROM event e
        JOIN stadium s ON e.stadium_id = s.id
        WHERE EXTRACT(month FROM e.event_date) = 12 AND EXTRACT(day FROM e.event_date) = 31
        ORDER BY e.start_time;
    ''')
    nye = cursor.fetchall()
    if nye:
        print('   New Years Eve:')
        for match in nye:
            print(f'     {match[1]} {match[2]} - {match[0]} at {match[3]}')

    print('\n📊 VENUE DISTRIBUTION:')
    cursor.execute('''
        SELECT s.name, COUNT(e.id) as match_count, AVG(e.attendance)::int as avg_attendance
        FROM event e
        JOIN stadium s ON e.stadium_id = s.id
        GROUP BY s.name
        ORDER BY match_count DESC, s.name;
    ''')
    venues = cursor.fetchall()
    for venue in venues:
        print(f'   {venue[0]:<35} | {venue[1]:2d} matches | {venue[2]:,} avg attendance')

    print('\n🗓️ UPCOMING MATCHES (Next 7 days):')
    cursor.execute('''
        SELECT e.event_name, e.event_date, e.start_time, s.name, 
               ht.team_name as home_team, at.team_name as away_team
        FROM event e
        JOIN stadium s ON e.stadium_id = s.id
        JOIN team ht ON e.home_team_id = ht.id
        JOIN team at ON e.away_team_id = at.id
        WHERE e.event_date >= CURRENT_DATE AND e.event_date <= CURRENT_DATE + INTERVAL '7 days'
        ORDER BY e.event_date, e.start_time
        LIMIT 10;
    ''')
    upcoming = cursor.fetchall()
    for match in upcoming:
        print(f'   {match[1]} {match[2]} - {match[4]} vs {match[5]}')
        print(f'     🏟️ {match[3]}')

    print('\n📈 TOURNAMENT SUMMARY:')
    cursor.execute('''
        SELECT 
            tournament_name,
            COUNT(*) as match_count,
            MIN(event_date) as start_date,
            MAX(event_date) as end_date,
            SUM(attendance) as total_attendance
        FROM event
        GROUP BY tournament_name
        ORDER BY start_date;
    ''')
    tournaments = cursor.fetchall()
    for tournament in tournaments:
        print(f'   {tournament[0]}:')
        print(f'     📅 {tournament[2]} to {tournament[3]}')
        print(f'     🎯 {tournament[1]} matches | 👥 {tournament[4]:,} total attendance')

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()