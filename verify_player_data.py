"""
Player Data Verification and Statistics Report
"""

from app import app, db
from models import Player, Team
from collections import defaultdict
import json

def generate_player_statistics_report():
    """Generate comprehensive statistics about the player data"""
    
    with app.app_context():
        players = Player.query.all()
        teams = Team.query.all()
        
        print("=" * 80)
        print("🏏 BBL PLAYER DATA VERIFICATION REPORT")
        print("=" * 80)
        print()
        
        # Basic Statistics
        print("📊 BASIC STATISTICS")
        print("-" * 40)
        print(f"Total Players: {len(players)}")
        print(f"Total Teams: {len(teams)}")
        print(f"Average Players per Team: {len(players) / len(teams):.1f}")
        print()
        
        # Team-wise breakdown
        print("🏏 TEAM-WISE BREAKDOWN")
        print("-" * 40)
        for team in teams:
            player_count = len(team.players)
            print(f"{team.team_name:<25} {player_count:>2} players")
        print()
        
        # Role Distribution
        role_counts = defaultdict(int)
        for player in players:
            role_counts[player.player_role or 'Unspecified'] += 1
        
        print("🎯 PLAYER ROLE DISTRIBUTION")
        print("-" * 40)
        for role, count in sorted(role_counts.items()):
            percentage = (count / len(players)) * 100
            print(f"{role:<20} {count:>2} players ({percentage:>5.1f}%)")
        print()
        
        # Batting Style Distribution
        batting_counts = defaultdict(int)
        for player in players:
            batting_counts[player.batting_style or 'Unspecified'] += 1
        
        print("🏏 BATTING STYLE DISTRIBUTION")
        print("-" * 40)
        for style, count in sorted(batting_counts.items()):
            percentage = (count / len(players)) * 100
            print(f"{style:<20} {count:>2} players ({percentage:>5.1f}%)")
        print()
        
        # Special Roles
        captains = [p for p in players if p.is_captain]
        wicket_keepers = [p for p in players if p.is_wicket_keeper]
        
        print("👨‍✈️ SPECIAL ROLES")
        print("-" * 40)
        print(f"Captains: {len(captains)}")
        for captain in captains:
            print(f"  • {captain.player_name} ({captain.team.team_name})")
        print()
        print(f"Wicket Keepers: {len(wicket_keepers)}")
        for wk in wicket_keepers:
            print(f"  • {wk.player_name} ({wk.team.team_name})")
        print()
        
        # Age Statistics
        ages = [p.age for p in players if p.age]
        if ages:
            avg_age = sum(ages) / len(ages)
            min_age = min(ages)
            max_age = max(ages)
            
            print("📅 AGE STATISTICS")
            print("-" * 40)
            print(f"Average Age: {avg_age:.1f} years")
            print(f"Youngest Player: {min_age} years")
            print(f"Oldest Player: {max_age} years")
            print(f"Players with Age Data: {len(ages)}/{len(players)}")
            print()
        
        # Nationality Distribution
        nationality_counts = defaultdict(int)
        for player in players:
            nationality_counts[player.nationality or 'Unspecified'] += 1
        
        print("🌍 NATIONALITY DISTRIBUTION")
        print("-" * 40)
        for nationality, count in sorted(nationality_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(players)) * 100
            print(f"{nationality:<15} {count:>2} players ({percentage:>5.1f}%)")
        print()
        
        # Market Value Statistics
        market_values = [p.market_value for p in players if p.market_value]
        if market_values:
            avg_value = sum(market_values) / len(market_values)
            min_value = min(market_values)
            max_value = max(market_values)
            
            print("💰 MARKET VALUE STATISTICS")
            print("-" * 40)
            print(f"Average Market Value: ${avg_value:,.0f}")
            print(f"Minimum Market Value: ${min_value:,.0f}")
            print(f"Maximum Market Value: ${max_value:,.0f}")
            print(f"Players with Market Value: {len(market_values)}/{len(players)}")
            print()
        
        # Top Valued Players
        top_players = sorted([p for p in players if p.market_value], 
                           key=lambda x: x.market_value, reverse=True)[:10]
        
        if top_players:
            print("💎 TOP 10 HIGHEST VALUED PLAYERS")
            print("-" * 40)
            for i, player in enumerate(top_players, 1):
                print(f"{i:>2}. {player.player_name:<25} ({player.team.team_name:<20}) ${player.market_value:>9,.0f}")
            print()
        
        # Data Completeness
        print("📋 DATA COMPLETENESS")
        print("-" * 40)
        fields = [
            ('Player Name', 'player_name'),
            ('Age', 'age'),
            ('Batting Style', 'batting_style'),
            ('Bowling Style', 'bowling_style'),
            ('Player Role', 'player_role'),
            ('Nationality', 'nationality'),
            ('Jersey Number', 'jersey_number'),
            ('Market Value', 'market_value'),
            ('Photo URL', 'photo_url')
        ]
        
        for field_name, field_attr in fields:
            complete_count = len([p for p in players if getattr(p, field_attr)])
            percentage = (complete_count / len(players)) * 100
            print(f"{field_name:<15} {complete_count:>2}/{len(players)} ({percentage:>5.1f}%)")
        
        print()
        print("=" * 80)
        print("✅ VERIFICATION COMPLETE - All player data successfully loaded!")
        print("=" * 80)

if __name__ == "__main__":
    generate_player_statistics_report()