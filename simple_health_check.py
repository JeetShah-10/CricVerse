#!/usr/bin/env python3
"""
Simple CricVerse System Health Check
Basic health monitoring without external dependencies
"""

import os
import sys
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available, environment variables may not be loaded")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleHealthMonitor:
    """Simple system health monitor"""
    
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
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self.checks.append(check)
        
        if not status:
            self.errors.append(f"{name}: {message}")
        
    def add_warning(self, message: str):
        """Add a warning message"""
        self.warnings.append(message)
        
    def check_environment_variables(self):
        """Check required environment variables"""
        required_vars = [
            'SECRET_KEY'
        ]
        
        optional_vars = [
            'DATABASE_URL',
            'PAYPAL_CLIENT_ID',
            'RAZORPAY_KEY_ID',
            'OPENAI_API_KEY',
            'GOOGLE_API_KEY'
        ]
        
        missing_required = []
        missing_optional = []
        present_optional = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
                
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
            else:
                present_optional.append(var)
                
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
            
        if present_optional:
            self.add_check(
                "Optional Environment Variables",
                True,
                f"Present: {', '.join(present_optional)}"
            )
            
        if missing_optional:
            self.add_warning(f"Optional variables missing: {', '.join(missing_optional)}")
            
    def check_file_permissions(self):
        """Check file and directory permissions"""
        check_paths = [
            'static',
            'static/qrcodes',
            'templates'
        ]
        
        permission_issues = []
        created_dirs = []
        
        for path in check_paths:
            try:
                # Create directory if it doesn't exist
                if not os.path.exists(path):
                    os.makedirs(path, exist_ok=True)
                    created_dirs.append(path)
                    
                # Test write permission
                if os.access(path, os.W_OK):
                    # Test actual write
                    test_file = os.path.join(path, 'test_write.tmp')
                    try:
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                    except Exception as e:
                        permission_issues.append(f"{path}: Cannot write test file - {e}")
                else:
                    permission_issues.append(f"{path}: No write permission")
                    
            except Exception as e:
                permission_issues.append(f"{path}: {e}")
                
        if not permission_issues:
            message = f"All directories accessible"
            if created_dirs:
                message += f" (created: {', '.join(created_dirs)})"
            self.add_check("File Permissions", True, message)
        else:
            self.add_check(
                "File Permissions", 
                False, 
                f"Issues: {'; '.join(permission_issues)}"
            )
            
    def check_python_modules(self):
        """Check critical Python modules"""
        critical_modules = [
            'flask',
            'flask_sqlalchemy', 
            'flask_login',
            'werkzeug',
            'jinja2'
        ]
        
        optional_modules = [
            'psycopg2',
            'redis',
            'celery',
            'qrcode',
            'PIL',
            'reportlab'
        ]
        
        missing_critical = []
        missing_optional = []
        present_optional = []
        
        for module in critical_modules:
            try:
                __import__(module)
            except ImportError:
                missing_critical.append(module)
                
        for module in optional_modules:
            try:
                __import__(module)
                present_optional.append(module)
            except ImportError:
                missing_optional.append(module)
                
        if not missing_critical:
            self.add_check(
                "Critical Python Modules", 
                True, 
                "All critical modules available"
            )
        else:
            self.add_check(
                "Critical Python Modules", 
                False, 
                f"Missing: {', '.join(missing_critical)}"
            )
            
        if present_optional:
            self.add_check(
                "Optional Python Modules",
                True,
                f"Available: {', '.join(present_optional)}"
            )
            
        if missing_optional:
            self.add_warning(f"Optional modules missing: {', '.join(missing_optional)}")
            
    def check_configuration_files(self):
        """Check for important configuration files"""
        config_files = [
            'app.py',
            'requirements.txt',
            '.env'
        ]
        
        missing_files = []
        present_files = []
        
        for file in config_files:
            if os.path.exists(file):
                present_files.append(file)
            else:
                missing_files.append(file)
                
        if len(present_files) >= 2:  # At least app.py and requirements.txt
            self.add_check(
                "Configuration Files",
                True,
                f"Found: {', '.join(present_files)}"
            )
        else:
            self.add_check(
                "Configuration Files",
                False,
                f"Missing critical files: {', '.join(missing_files)}"
            )
            
        if missing_files:
            self.add_warning(f"Missing files: {', '.join(missing_files)}")
            
    def check_database_config(self):
        """Check database configuration"""
        db_url = os.getenv('DATABASE_URL')
        
        if db_url:
            if 'postgresql' in db_url.lower():
                db_type = 'PostgreSQL'
            elif 'sqlite' in db_url.lower():
                db_type = 'SQLite'
            else:
                db_type = 'Unknown'
                
            self.add_check(
                "Database Configuration",
                True,
                f"Database configured: {db_type}",
                {"type": db_type}
            )
        else:
            self.add_check(
                "Database Configuration",
                False,
                "No DATABASE_URL configured - will use SQLite fallback"
            )
            
    def run_all_checks(self):
        """Run all health checks"""
        print("🏥 Running CricVerse System Health Checks...")
        print("=" * 50)
        
        self.check_environment_variables()
        self.check_configuration_files()
        self.check_database_config()
        self.check_python_modules()
        self.check_file_permissions()
            
    def generate_report(self) -> Dict[str, Any]:
        """Generate health check report"""
        total_checks = len(self.checks)
        passed_checks = sum(1 for check in self.checks if check['status'] == 'PASS')
        failed_checks = total_checks - passed_checks
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'total_checks': total_checks,
                'passed': passed_checks,
                'failed': failed_checks,
                'success_rate': round((passed_checks / total_checks) * 100, 1) if total_checks > 0 else 0
            },
            'checks': self.checks,
            'errors': self.errors,
            'warnings': self.warnings,
            'status': 'HEALTHY' if failed_checks == 0 else 'DEGRADED' if failed_checks <= 2 else 'UNHEALTHY'
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
            print(f"\n🚨 Issues Found:")
            for error in self.errors:
                print(f"   • {error}")
                
        print(f"\n💡 Recommendations:")
        if failed_checks := summary['failed']:
            if failed_checks <= 2:
                print("   • System is in degraded state but should still function")
                print("   • Address the failed checks when possible")
            else:
                print("   • System has multiple issues that may affect functionality")
                print("   • Address critical issues before running in production")
        else:
            print("   • System appears healthy and ready for operation")
            
        if self.warnings:
            print("   • Consider installing optional modules for enhanced functionality")
            
        print("\n" + "=" * 50)

def main():
    """Main health check function"""
    monitor = SimpleHealthMonitor()
    monitor.run_all_checks()
    monitor.print_report()
    
    # Return appropriate exit code
    report = monitor.generate_report()
    if report['status'] == 'UNHEALTHY':
        sys.exit(1)
    elif report['status'] == 'DEGRADED':
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()