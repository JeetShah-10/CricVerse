#!/usr/bin/env python3
"""
CricVerse Master Fixer & Tester
Orchestrates the complete process of diagnosing, fixing, and testing the CricVerse website
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Load environment early so DATABASE_URL and keys are available
try:
    from dotenv import load_dotenv
    if Path('cricverse.env').exists():
        load_dotenv('cricverse.env')
    else:
        load_dotenv()
except Exception:
    pass

# Ensure UTF-8 for all child processes to avoid Unicode issues on Windows
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
os.environ.setdefault('PYTHONUTF8', '1')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CricVerseMasterFixer:
    """Master orchestrator for CricVerse website fixes and testing"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.phase_results = {}
        self.overall_success = True
        # Pass current environment to subprocesses explicitly
        self.subprocess_env = {**os.environ}
        self.subprocess_env['PYTHONIOENCODING'] = 'utf-8'
        self.subprocess_env['PYTHONUTF8'] = '1'
    
    def run_script(self, script_name, description, timeout=300):
        """Run a Python script and capture results"""
        logger.info(f"\n{'='*60}")
        logger.info(f"PHASE: {description}")
        logger.info(f"Running: {script_name}")
        logger.info(f"{'='*60}")
        
        phase_start = datetime.now()
        
        try:
            # Check if script exists
            if not os.path.exists(script_name):
                logger.error(f"Script not found: {script_name}")
                self.phase_results[description] = {
                    'success': False,
                    'error': f'Script not found: {script_name}',
                    'duration': 0
                }
                return False
            
            # Run the script
            result = subprocess.run(
                [sys.executable, script_name],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
                cwd=os.getcwd(),
                env=self.subprocess_env,
            )
            
            phase_end = datetime.now()
            duration = (phase_end - phase_start).total_seconds()
            
            success = result.returncode == 0
            stdout = result.stdout or ''
            stderr = result.stderr or ''
            output = stdout + stderr
            
            # Store results
            self.phase_results[description] = {
                'success': success,
                'returncode': result.returncode,
                'output': output[:2000],  # Limit output size
                'duration': duration,
                'timestamp': phase_end.isoformat()
            }
            
            if success:
                logger.info(f"✅ {description} completed successfully ({duration:.2f}s)")
            else:
                logger.error(f"❌ {description} failed ({duration:.2f}s)")
                logger.error(f"Error output: {output[:500]}")
                self.overall_success = False
            
            return success
            
        except subprocess.TimeoutExpired:
            duration = timeout
            error_msg = f"Script timed out after {timeout} seconds"
            logger.error(f"❌ {error_msg}")
            
            self.phase_results[description] = {
                'success': False,
                'error': error_msg,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            }
            self.overall_success = False
            return False
            
        except Exception as e:
            phase_end = datetime.now()
            duration = (phase_end - phase_start).total_seconds()
            error_msg = f"Exception running script: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            self.phase_results[description] = {
                'success': False,
                'error': error_msg,
                'duration': duration,
                'timestamp': phase_end.isoformat()
            }
            self.overall_success = False
            return False
    
    def check_prerequisites(self):
        """Check if all required files and dependencies are available"""
        logger.info("🔍 Checking prerequisites...")
        
        required_files = [
            'run.py',
            'app/__init__.py',
            'chatbot.py',
            'requirements.txt'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"Missing required files: {missing_files}")
            return False
        
        # Check if virtual environment is activated
        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            logger.warning("⚠️ Virtual environment not detected - some dependencies might not be available")
        
        logger.info("✅ Prerequisites check completed")
        return True
    
    def create_scripts_if_missing(self):
        """Create diagnostic and fix scripts if they don't exist"""
        scripts_to_check = [
            'comprehensive_diagnostics.py',
            'fix_cricverse_issues.py',
            'run_comprehensive_tests.py'
        ]
        
        missing_scripts = []
        for script in scripts_to_check:
            if not os.path.exists(script):
                missing_scripts.append(script)
        
        if missing_scripts:
            logger.warning(f"Missing scripts: {missing_scripts}")
            logger.info("These scripts should have been created in previous steps")
            return False
        
        return True
    
    def run_comprehensive_workflow(self):
        """Run the complete CricVerse fixing and testing workflow"""
        logger.info("🚀 Starting CricVerse Master Fixing & Testing Workflow")
        logger.info(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Phase 1: Prerequisites Check
        if not self.check_prerequisites():
            logger.error("❌ Prerequisites check failed - aborting workflow")
            return False
        
        if not self.create_scripts_if_missing():
            logger.error("❌ Required scripts missing - aborting workflow")
            return False
        
        # Phase 2: Initial Diagnostics
        logger.info("\n🔬 PHASE 1: INITIAL DIAGNOSTICS")
        diagnostics_success = self.run_script(
            'comprehensive_diagnostics.py',
            'Initial System Diagnostics',
            timeout=180
        )
        
        # Phase 3: Apply Fixes (regardless of diagnostics result)
        logger.info("\n🔧 PHASE 2: APPLYING FIXES")
        fixes_success = self.run_script(
            'fix_cricverse_issues.py',
            'System Fixes Application',
            timeout=120
        )
        
        # Phase 4: Post-Fix Diagnostics
        logger.info("\n🔬 PHASE 3: POST-FIX DIAGNOSTICS")
        post_diagnostics_success = self.run_script(
            'comprehensive_diagnostics.py',
            'Post-Fix System Diagnostics',
            timeout=180
        )
        
        # Phase 5: Comprehensive Testing
        logger.info("\n🧪 PHASE 4: COMPREHENSIVE TESTING")
        testing_success = self.run_script(
            'run_comprehensive_tests.py',
            'Comprehensive System Testing',
            timeout=300
        )
        
        # Phase 6: Final Validation
        logger.info("\n✅ PHASE 5: FINAL VALIDATION")
        self.run_final_validation()
        
        # Generate final report
        self.generate_master_report()
        
        return self.overall_success
    
    def run_final_validation(self):
        """Run final validation checks"""
        logger.info("Running final validation...")
        
        validation_results = {
            'database_connection': False,
            'flask_app_startup': False,
            'chatbot_functionality': False,
            'critical_files_present': False
        }
        
        try:
            # Test database connection
            from sqlalchemy import create_engine, text
            db_url = os.getenv('DATABASE_URL')
            if db_url:
                if db_url.startswith('postgresql://'):
                    db_url = db_url.replace('postgresql://', 'postgresql+pg8000://', 1)
                engine = create_engine(db_url)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                validation_results['database_connection'] = True
                logger.info("✅ Database connection validated")
            else:
                logger.warning("⚠️ DATABASE_URL not configured")
        except Exception as e:
            logger.error(f"❌ Database validation failed: {e}")
        
        try:
            # Test Flask app startup
            sys.path.insert(0, os.getcwd())
            from app import create_app
            app = create_app('default')
            validation_results['flask_app_startup'] = True
            logger.info("✅ Flask app startup validated")
        except Exception as e:
            logger.error(f"❌ Flask app validation failed: {e}")
        
        try:
            # Test chatbot functionality
            from chatbot import get_chatbot_response
            response = get_chatbot_response("test", user_id="validation_test")
            if response:
                validation_results['chatbot_functionality'] = True
                logger.info("✅ Chatbot functionality validated")
            else:
                logger.warning("⚠️ Chatbot returned empty response")
        except Exception as e:
            logger.error(f"❌ Chatbot validation failed: {e}")
        
        # Check critical files
        critical_files = ['run.py', 'app/__init__.py', 'chatbot.py', 'templates/index.html']
        all_present = all(os.path.exists(f) for f in critical_files)
        validation_results['critical_files_present'] = all_present
        
        if all_present:
            logger.info("✅ Critical files validated")
        else:
            missing = [f for f in critical_files if not os.path.exists(f)]
            logger.error(f"❌ Missing critical files: {missing}")
        
        # Store validation results
        self.phase_results['Final Validation'] = {
            'success': all(validation_results.values()),
            'details': validation_results,
            'duration': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        if all(validation_results.values()):
            logger.info("✅ Final validation passed")
        else:
            logger.error("❌ Final validation failed")
            self.overall_success = False
    
    def generate_master_report(self):
        """Generate comprehensive master report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate phase statistics
        successful_phases = sum(1 for result in self.phase_results.values() if result['success'])
        total_phases = len(self.phase_results)
        success_rate = (successful_phases / total_phases * 100) if total_phases > 0 else 0
        
        # Create comprehensive report
        master_report = {
            'workflow_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration_seconds': total_duration,
                'total_phases': total_phases,
                'successful_phases': successful_phases,
                'failed_phases': total_phases - successful_phases,
                'overall_success_rate': success_rate,
                'overall_success': self.overall_success
            },
            'phase_results': self.phase_results,
            'recommendations': self.generate_recommendations()
        }
        
        # Save master report
        with open('cricverse_master_report.json', 'w') as f:
            json.dump(master_report, f, indent=2)
        
        # Print summary
        logger.info(f"\n{'='*80}")
        logger.info("CRICVERSE MASTER WORKFLOW SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Total Duration: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")
        logger.info(f"Phases Completed: {successful_phases}/{total_phases} ({success_rate:.1f}%)")
        logger.info(f"Overall Success: {'✅ YES' if self.overall_success else '❌ NO'}")
        
        logger.info(f"\n📊 PHASE BREAKDOWN:")
        for phase_name, result in self.phase_results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            duration = result.get('duration', 0)
            logger.info(f"  {status} - {phase_name} ({duration:.2f}s)")
        
        if not self.overall_success:
            logger.info(f"\n🚨 ISSUES DETECTED:")
            failed_phases = [name for name, result in self.phase_results.items() if not result['success']]
            for i, phase in enumerate(failed_phases, 1):
                logger.info(f"   {i}. {phase}")
        
        logger.info(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(self.generate_recommendations(), 1):
            logger.info(f"   {i}. {rec}")
        
        logger.info(f"\n📄 Detailed report saved to: cricverse_master_report.json")
        
        return master_report
    
    def generate_recommendations(self):
        """Generate recommendations based on results"""
        recommendations = []
        
        if not self.overall_success:
            recommendations.append("Review failed phases and address critical issues")
        
        # Check specific phase failures
        if 'Initial System Diagnostics' in self.phase_results and not self.phase_results['Initial System Diagnostics']['success']:
            recommendations.append("Database connectivity issues detected - verify Supabase configuration")
        
        if 'System Fixes Application' in self.phase_results and not self.phase_results['System Fixes Application']['success']:
            recommendations.append("Fix application failed - manually review and apply fixes")
        
        if 'Comprehensive System Testing' in self.phase_results and not self.phase_results['Comprehensive System Testing']['success']:
            recommendations.append("Testing phase failed - review test failures and fix underlying issues")
        
        if 'Final Validation' in self.phase_results:
            validation = self.phase_results['Final Validation']
            if not validation['success']:
                details = validation.get('details', {})
                if not details.get('database_connection', True):
                    recommendations.append("Configure DATABASE_URL in environment file")
                if not details.get('chatbot_functionality', True):
                    recommendations.append("Configure AI API keys (OpenAI or Gemini)")
                if not details.get('flask_app_startup', True):
                    recommendations.append("Fix Flask application startup issues")
        
        # General recommendations
        if self.overall_success:
            recommendations.extend([
                "System is working well - consider running performance optimizations",
                "Set up monitoring and logging for production deployment",
                "Create regular backup procedures for database and configuration"
            ])
        else:
            recommendations.extend([
                "Run individual diagnostic scripts to identify specific issues",
                "Check environment configuration and API keys",
                "Verify all dependencies are installed correctly"
            ])
        
        return recommendations

def main():
    """Main execution"""
    logger.info("🎯 CricVerse Master Fixer & Tester")
    logger.info("=" * 50)
    
    # Create and run master fixer
    master_fixer = CricVerseMasterFixer()
    success = master_fixer.run_comprehensive_workflow()
    
    if success:
        logger.info("\n🎉 CricVerse website is now working perfectly!")
        logger.info("You can start the application with: python run.py")
        sys.exit(0)
    else:
        logger.error("\n⚠️ Some issues remain - check the master report for details")
        logger.info("Review the recommendations and run specific fixes as needed")
        sys.exit(1)

if __name__ == "__main__":
    main()
