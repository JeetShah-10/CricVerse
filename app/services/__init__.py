"""
CricVerse Services Module
Centralized service initialization and management
All services integrated with Supabase database
Big Bash League Cricket Platform
"""

import logging
from typing import Dict, Any, Optional
from flask import Flask

# Import all services
from .supabase_service import supabase_service
from .analytics_service import analytics_service
from .enhanced_booking_service import enhanced_booking_service
from .performance_service import performance_service
from .security_service import security_service
from .live_cricket_service import live_cricket_service

# Configure logging
logger = logging.getLogger(__name__)

class ServiceManager:
    """Manages all CricVerse services"""
    
    def __init__(self):
        self.services = {}
        self.initialized = False
    
    def init_app(self, app: Flask, socketio_instance=None) -> None:
        """Initialize all services with Flask app"""
        try:
            logger.info("🚀 Initializing CricVerse services...")
            
            # Initialize core services in order
            services_to_init = [
                ('supabase', supabase_service),
                ('analytics', analytics_service),
                ('enhanced_booking', enhanced_booking_service),
                ('performance', performance_service),
                ('security', security_service),
                ('live_cricket', live_cricket_service)
            ]
            
            for service_name, service in services_to_init:
                try:
                    if hasattr(service, 'init_app'):
                        if service_name == 'live_cricket' and socketio_instance:
                            service.init_app(app, socketio_instance)
                        else:
                            service.init_app(app)
                        self.services[service_name] = service
                        logger.info(f"✅ {service_name} service initialized")
                    else:
                        logger.warning(f"⚠️ {service_name} service missing init_app method")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize {service_name} service: {str(e)}")
                    # Continue with other services
            
            self.initialized = True
            logger.info(f"🎉 Service manager initialized with {len(self.services)} services")
            
        except Exception as e:
            logger.error(f"❌ Service manager initialization failed: {str(e)}")
            raise
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a specific service by name"""
        return self.services.get(service_name)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        status = {
            'initialized': self.initialized,
            'total_services': len(self.services),
            'services': {}
        }
        
        for name, service in self.services.items():
            try:
                # Check if service has health check
                if hasattr(service, 'health_check'):
                    service_status = service.health_check()
                elif hasattr(service, 'initialized'):
                    service_status = {'status': 'healthy' if service.initialized else 'unhealthy'}
                else:
                    service_status = {'status': 'unknown'}
                
                status['services'][name] = service_status
            except Exception as e:
                status['services'][name] = {'status': 'error', 'error': str(e)}
        
        return status
    
    def shutdown(self) -> None:
        """Shutdown all services gracefully"""
        logger.info("🔄 Shutting down services...")
        
        for name, service in self.services.items():
            try:
                if hasattr(service, 'shutdown'):
                    service.shutdown()
                    logger.info(f"✅ {name} service shutdown complete")
            except Exception as e:
                logger.error(f"❌ Error shutting down {name} service: {str(e)}")
        
        self.services.clear()
        self.initialized = False
        logger.info("🔄 All services shutdown complete")

# Global service manager instance
service_manager = ServiceManager()

# Export all services for easy import
__all__ = [
    'service_manager',
    'supabase_service',
    'analytics_service', 
    'enhanced_booking_service',
    'performance_service',
    'security_service',
    'live_cricket_service'
]

# Service initialization function for Flask app
def init_services(app: Flask, socketio_instance=None) -> None:
    """Initialize all services with Flask app"""
    service_manager.init_app(app, socketio_instance)

# Health check endpoint data
def get_services_health() -> Dict[str, Any]:
    """Get health status of all services"""
    return service_manager.get_service_status()
