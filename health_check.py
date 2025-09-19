#!/usr/bin/env python3
"""
CricVerse System Health Check and Error Monitor
Monitors system health and provides diagnostic information
"""

import os
import sys
import psutil
from dotenv import load_dotenv

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests

# Load environment from local files (best-effort)
try:
    if os.path.exists('cricverse.env'):
        load_dotenv('cricverse.env')
    else:
        load_dotenv()
except Exception:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemHealthMonitor:
    """Monitor system health and performance"""
    
    def __init__(self):
        self.checks = []
        self.errors = []
        self.warnings = []
        
    def add_check(self, name: str, status: bool, message: str = "", details: Optional[Dict[str, Any]] = None):
        """Add a health check result"""
        check = {
            'name': name,
            'status': 'PASS' if status else 'FAIL',
            'message': message,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        self.checks.append(check)
        
        if not status:
            self.errors.append(f"{name}: {message}")
        
    def add_warning(self, message: str):
        """Add a warning message"""
        self.warnings.append(message)
        
    def check_database_connection(self):
        """Check database connectivity"""
        try:
            # This would normally test the actual database connection
            # For now, just check if the environment variables are set
            db_url = os.getenv('DATABASE_URL')
            if db_url:
                self.add_check(
                    "Database Configuration", 
                    True, 
                    "Database URL configured",
                    {"db_type": "PostgreSQL" if "postgresql" in db_url else "SQLite"}
                )
            else:
                self.add_check(
                    "Database Configuration", 
                    False, 
                    "DATABASE_URL not configured"
                )
        except Exception as e:
            self.add_check("Database Connection", False, f"Database error: {e}")
            
    def check_redis_connection(self):
        """Check Redis connectivity for caching and rate limiting"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=2)
            r.ping()
            self.add_check("Redis Connection", True, "Redis is available")
        except Exception as e:
            self.add_check(
                "Redis Connection", 
                False, 
                "Redis not available - using in-memory fallback",
                {"error": str(e)}
            )
            
    def check_environment_variables(self):
        """Check required environment variables"""
        required_vars = [
            'SECRET_KEY',
            'DATABASE_URL'
        ]
        
        optional_vars = [
            'PAYPAL_CLIENT_ID',
            'RAZORPAY_KEY_ID',
            'OPENAI_API_KEY',
            'GOOGLE_API_KEY'
        ]
        
        missing_required = []
        missing_optional = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
                
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
                
        if not missing_required:
            self.add_check(
                "Required Environment Variables", 
                True, 
                "All required variables set"
            )
        else:
            self.add_check(
                "Required Environment Variables", 
                False, 
                f"Missing: {', '.join(missing_required)}"
            )
            
        if missing_optional:
            self.add_warning(f"Optional variables missing: {', '.join(missing_optional)}")
            
    def check_file_permissions(self):
        """Check file and directory permissions"""
        check_paths = [
            'static/qrcodes',
            'logs',
            'uploads'
        ]
        
        permission_issues = []
        
        for path in check_paths:
            try:
                # Create directory if it doesn't exist
                if not os.path.exists(path):
                    os.makedirs(path, exist_ok=True)
                    
                # Test write permission
                test_file = os.path.join(path, 'test_write.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                
            except Exception as e:
                permission_issues.append(f"{path}: {e}")
                
        if not permission_issues:
            self.add_check("File Permissions", True, "All directories writable")
        else:
            self.add_check(
                "File Permissions", 
                False, 
                f"Permission issues: {'; '.join(permission_issues)}"
            )
            
    def check_system_resources(self):
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Check if resources are within acceptable limits
            resource_ok = (
                cpu_percent < 80 and 
                memory_percent < 85 and 
                disk_percent < 90
            )
            
            details = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'available_memory_gb': round(memory.available / (1024**3), 2)
            }
            
            if resource_ok:
                self.add_check(
                    "System Resources", 
                    True, 
                    "Resource usage within limits",
                    details
                )
            else:
                warnings = []
                if cpu_percent >= 80:
                    warnings.append(f"High CPU usage: {cpu_percent}%")
                if memory_percent >= 85:
                    warnings.append(f"High memory usage: {memory_percent}%")
                if disk_percent >= 90:
                    warnings.append(f"High disk usage: {disk_percent}%")
                    
                self.add_check(
                    "System Resources", 
                    False, 
                    "; ".join(warnings),
                    details
                )
                
        except Exception as e:
            self.add_check("System Resources", False, f"Cannot check resources: {e}")
            
    def check_application_health(self, app_url: str = "http://localhost:5000"):
        """Check if the application is responding"""
        try:
            response = requests.get(app_url, timeout=10)
            if response.status_code == 200:
                self.add_check(
                    "Application Health", 
                    True, 
                    f"Application responding on {app_url}",
                    {"status_code": response.status_code}
                )
            else:
                self.add_check(
                    "Application Health", 
                    False, 
                    f"Application returned status {response.status_code}"
                )
        except requests.exceptions.ConnectionError:
            self.add_check(
                "Application Health", 
                False, 
                f"Cannot connect to application at {app_url}"
            )
        except Exception as e:
            self.add_check("Application Health", False, f"Health check failed: {e}")
            
    def run_all_checks(self, include_app_check: bool = False, app_url: str = "http://localhost:5000"):
        """Run all health checks"""
        print("🏥 Running CricVerse System Health Checks...")
        print("=" * 50)
        
        self.check_environment_variables()
        self.check_database_connection()
        self.check_redis_connection()
        self.check_file_permissions()
        self.check_system_resources()
        
        if include_app_check:
            self.check_application_health(app_url)
            
    def generate_report(self) -> Dict[str, Any]:
        """Generate health check report"""
        total_checks = len(self.checks)
        passed_checks = sum(1 for check in self.checks if check['status'] == 'PASS')
        failed_checks = total_checks - passed_checks
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_checks': total_checks,
                'passed': passed_checks,
                'failed': failed_checks,
                'success_rate': round((passed_checks / total_checks) * 100, 1) if total_checks > 0 else 0
            },
            'checks': self.checks,
            'errors': self.errors,
            'warnings': self.warnings,
            'status': 'HEALTHY' if failed_checks == 0 else 'UNHEALTHY'
        }
        
    def print_report(self):
        """Print formatted health check report"""
        report = self.generate_report()
        summary = report['summary']
        
        print(f"\n📊 Health Check Summary:")
        print(f"   Total Checks: {summary['total_checks']}")
        print(f"   Passed: {summary['passed']} ✅")
        print(f"   Failed: {summary['failed']} ❌")
        print(f"   Success Rate: {summary['success_rate']}%")
        print(f"   Overall Status: {report['status']}")
        
        print(f"\n📋 Detailed Results:")
        for check in self.checks:
            status_icon = "✅" if check['status'] == 'PASS' else "❌"
            print(f"   {status_icon} {check['name']}: {check['message']}")
            
        if self.warnings:
            print(f"\n⚠️ Warnings:")
            for warning in self.warnings:
                print(f"   • {warning}")
                
        if self.errors:
            print(f"\n🚨 Critical Issues:")
            for error in self.errors:
                print(f"   • {error}")
                
        print("\n" + "=" * 50)

def main():
    """Main health check function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--with-app':
        include_app = True
        app_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5000"
    else:
        include_app = False
        app_url = "http://localhost:5000"
        
    monitor = SystemHealthMonitor()
    monitor.run_all_checks(include_app_check=include_app, app_url=app_url)
    monitor.print_report()
    
    # Exit with error code if there are failures
    report = monitor.generate_report()
    if report['summary']['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()