"""
Supabase Configuration for CricVerse
Handles Supabase connection and validation
"""

import os
import logging
from supabase import create_client, Client
from typing import Optional

logger = logging.getLogger(__name__)

class SupabaseConfig:
    """Supabase configuration and connection manager"""
    
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        logger.info(f"[DEBUG] SupabaseConfig init - URL: {self.url is not None}, Key: {self.key is not None}")
        logger.info(f"[DEBUG] Raw URL: {self.url}")
        logger.info(f"[DEBUG] Raw Key: {self.key}")

        self.client: Optional[Client] = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("✅ Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Supabase client: {e}")
    
    def validate_config(self) -> bool:
        """Validate Supabase configuration"""
        if not self.url:
            logger.warning("SUPABASE_URL not found in environment variables")
            return False
        
        if not self.key:
            logger.warning("SUPABASE_ANON_KEY not found in environment variables")
            return False
        
        return True
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        if not self.client:
            return False
        
        try:
            # Try to fetch from a table to test connection
            response = self.client.table('team').select('id').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False
    
    def get_client(self) -> Optional[Client]:
        """Get Supabase client instance"""
        return self.client

# Global instance
supabase_config = SupabaseConfig()
