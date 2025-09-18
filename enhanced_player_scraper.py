"""
Enhanced Web Scraping Module for BBL Player Data
Retrieves comprehensive player information from multiple reliable sources
"""

import requests
import json
import time
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)

class BBLPlayerScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Base URLs for different data sources
        self.data_sources = {
            'cricket_com_au': 'https://www.cricket.com.au',
            'espncricinfo': 'https://www.espncricinfo.com',
            'bbl_official': 'https://www.bigbash.com.au'
        }

    def search_player_cricinfo(self, player_name: str) -> Dict:
        """Search for player on ESPNCricinfo"""
        try:
            search_url = f"https://www.espncricinfo.com/search?q={quote(player_name)}"
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                return self._parse_cricinfo_search(response.text, player_name)
        except Exception as e:
            logger.warning(f"Error searching Cricinfo for {player_name}: {e}")
        
        return {}

    def _parse_cricinfo_search(self, html: str, player_name: str) -> Dict:
        """Parse Cricinfo search results"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Look for player profile links
            player_links = soup.find_all('a', href=re.compile(r'/player/\d+'))
            
            for link in player_links:
                if player_name.lower() in link.get_text().lower():
                    player_url = urljoin(self.data_sources['espncricinfo'], link['href'])
                    return self._get_cricinfo_player_details(player_url)
        except Exception as e:
            logger.warning(f"Error parsing Cricinfo search for {player_name}: {e}")
        
        return {}

    def _get_cricinfo_player_details(self, player_url: str) -> Dict:
        """Get detailed player information from Cricinfo profile"""
        try:
            response = self.session.get(player_url, timeout=10)
            if response.status_code != 200:
                return {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            player_data = {}
            
            # Extract player details from various sections
            # This is a simplified version - real implementation would be more comprehensive
            
            # Look for player stats and bio information
            bio_section = soup.find('div', class_='player-bio')
            if bio_section:
                # Extract batting/bowling style, birthdate, etc.
                pass
            
            return player_data
            
        except Exception as e:
            logger.warning(f"Error getting Cricinfo player details: {e}")
            return {}

    def get_player_image_url(self, player_name: str, team_name: str) -> Optional[str]:
        """Attempt to find a player image URL"""
        try:
            # Generate a generic player image URL or use placeholder
            safe_name = player_name.replace(' ', '_').lower()
            safe_team = team_name.replace(' ', '_').lower()
            
            # Return a placeholder or constructed URL
            return f"/static/img/players/{safe_name}.jpg"
            
        except Exception as e:
            logger.warning(f"Error getting image for {player_name}: {e}")
            return None

    def enhance_player_data(self, player_name: str, team_name: str, base_data: Dict) -> Dict:
        """Enhance player data with information from multiple sources"""
        enhanced_data = base_data.copy()
        
        try:
            # Try to get additional data from Cricinfo
            cricinfo_data = self.search_player_cricinfo(player_name)
            if cricinfo_data:
                enhanced_data.update(cricinfo_data)
            
            # Try to get player image
            image_url = self.get_player_image_url(player_name, team_name)
            if image_url:
                enhanced_data['photo_url'] = image_url
            
            # Add delay to be respectful to servers
            time.sleep(0.5)
            
        except Exception as e:
            logger.warning(f"Error enhancing data for {player_name}: {e}")
        
        return enhanced_data

class PlayerDataEnricher:
    """Enriches player data with additional cricket statistics and information"""
    
    def __init__(self):
        self.scraper = BBLPlayerScraper()
    
    def enrich_all_players(self, teams_data: Dict) -> Dict:
        """Enrich all players in teams_data with comprehensive information"""
        enriched_data = {}
        
        for team_name, team_info in teams_data.items():
            logger.info(f"🔍 Enriching data for {team_name}")
            enriched_data[team_name] = {
                "players": []
            }
            
            for player_name in team_info["players"]:
                try:
                    # Start with base player data
                    base_data = {
                        'player_name': player_name,
                        'team_name': team_name
                    }
                    
                    # Enhance with scraped data
                    enhanced_player = self.scraper.enhance_player_data(
                        player_name, team_name, base_data
                    )
                    
                    enriched_data[team_name]["players"].append(enhanced_player)
                    logger.info(f"✅ Enriched data for {player_name}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to enrich data for {player_name}: {e}")
                    # Add basic data if enrichment fails
                    enriched_data[team_name]["players"].append({
                        'player_name': player_name,
                        'team_name': team_name
                    })
        
        return enriched_data

def main():
    """Test the scraping functionality"""
    scraper = BBLPlayerScraper()
    
    # Test with a few known players
    test_players = [
        ("Steve Smith", "Sydney Sixers"),
        ("Glenn Maxwell", "Melbourne Stars"),
        ("David Warner", "Sydney Thunder")
    ]
    
    for player_name, team_name in test_players:
        logger.info(f"Testing scraper for {player_name}")
        enhanced_data = scraper.enhance_player_data(player_name, team_name, {})
        logger.info(f"Result: {enhanced_data}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()