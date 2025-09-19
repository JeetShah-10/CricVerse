#!/usr/bin/env python3
"""
Comprehensive CricVerse Test Runner
Identifies, categorizes, and runs all test files systematically
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure UTF-8 encoding for all subprocesses (fixes Windows cp1252 UnicodeEncodeError)
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
os.environ.setdefault('PYTHONUTF8', '1')

class CricVerseTestRunner:
    """Comprehensive test runner for CricVerse"""
    
    def __init__(self):
        self.test_results = {}
        self.test_categories = defaultdict(list)
        self.failed_tests = []
        self.passed_tests = []
        
    def analyze_test_file(self, file_path):
        """Analyze a test file to determine its category and characteristics"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine test framework
            framework = 'unknown'
            if 'import unittest' in content or 'from unittest' in content:
                framework = 'unittest'
            elif 'import pytest' in content or 'from pytest' in content:
                framework = 'pytest'
            elif 'test_client' in content:
                framework = 'flask_test'
            
            # Determine category based on content
            category = 'general'
            if any(word in content.lower() for word in ['database', 'db', 'supabase', 'postgresql']):
                category = 'database'
            elif any(word in content.lower() for word in ['chatbot', 'ai', 'openai', 'gemini']):
                category = 'chatbot'
            elif any(word in content.lower() for word in ['booking', 'ticket', 'reservation']):
                category = 'booking'
            elif any(word in content.lower() for word in ['auth', 'login', 'user', 'customer']):
                category = 'authentication'
            elif any(word in content.lower() for word in ['payment', 'razorpay', 'paypal']):
                category = 'payment'
            elif any(word in content.lower() for word in ['qr', 'code', 'generation']):
                category = 'qr_codes'
            elif any(word in content.lower() for word in ['notification', 'email', 'sms']):
                category = 'notifications'
            elif any(word in content.lower() for word in ['websocket', 'socketio', 'realtime']):
                category = 'realtime'
            elif any(word in content.lower() for word in ['admin', 'management']):
                category = 'admin'
            elif any(word in content.lower() for word in ['route', 'endpoint', 'api']):
                category = 'routes'
            
            # Check if file seems current/relevant
            is_current = True
            if any(word in content for word in ['deprecated', 'old', 'legacy']):
                is_current = False
            
            # Get file stats
            stat = file_path.stat()
            
            analysis = {
                'file': str(file_path),
                'framework': framework,
                'category': category,
                'size': len(content),
                'lines': len(content.split('\n')),
                'is_current': is_current,
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'has_main': '__main__' in content,
                'test_count_estimate': content.count('def test_')
            }
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Could not analyze {file_path}: {e}")
            return None
    
    def discover_test_files(self):
        """Discover and categorize all test files"""
        logger.info("🔍 Discovering test files...")
        
        # Find all test files
        test_patterns = ['test_*.py', '*_test.py']
        test_files = []
        
        for pattern in test_patterns:
            test_files.extend(Path('.').glob(pattern))
            test_files.extend(Path('.').glob(f'**/{pattern}'))
        
        # Remove duplicates
        test_files = list(set(test_files))
        
        logger.info(f"Found {len(test_files)} test files")
        
        # Analyze each test file
        for test_file in test_files:
            analysis = self.analyze_test_file(test_file)
            if analysis:
                self.test_categories[analysis['category']].append(analysis)
        
        # Sort by last modified (newest first) within each category
        for category in self.test_categories:
            self.test_categories[category].sort(
                key=lambda x: x['last_modified'], 
                reverse=True
            )
        
        return self.test_categories
    
    def run_unittest_file(self, test_info):
        """Run a unittest-based test file"""
        file_path = test_info['file']
        logger.info(f"Running unittest: {file_path}")
        
        try:
            result = subprocess.run(
                [sys.executable, file_path],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.getcwd(),
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'}
            )
            
            # Parse results
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            # Extract test counts if available
            test_count = 0
            passed_count = 0
            failed_count = 0
            
            if 'Ran ' in output:
                try:
                    ran_line = [line for line in output.split('\n') if line.startswith('Ran ')][0]
                    test_count = int(ran_line.split(' ')[1])
                    if success:
                        passed_count = test_count
                    else:
                        # Try to extract failure count
                        if 'FAILED' in output:
                            failed_count = output.count('FAILED')
                            passed_count = test_count - failed_count
                except:
                    pass
            
            return {
                'success': success,
                'output': output[:1000],  # Limit output size
                'test_count': test_count,
                'passed': passed_count,
                'failed': failed_count,
                'duration': 'N/A'
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': 'Test timed out after 60 seconds',
                'test_count': 0,
                'passed': 0,
                'failed': 1,
                'duration': '60+'
            }
        except Exception as e:
            return {
                'success': False,
                'output': f'Exception: {str(e)}',
                'test_count': 0,
                'passed': 0,
                'failed': 1,
                'duration': 'N/A'
            }
    
    def run_pytest_file(self, test_info):
        """Run a pytest-based test file"""
        file_path = test_info['file']
        logger.info(f"Running pytest: {file_path}")
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', file_path, '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.getcwd(),
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'}
            )
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            # Parse pytest output
            test_count = 0
            passed_count = 0
            failed_count = 0
            
            if '::' in output:
                test_count = output.count('::')
                passed_count = output.count('PASSED')
                failed_count = output.count('FAILED')
            
            return {
                'success': success,
                'output': output[:1000],
                'test_count': test_count,
                'passed': passed_count,
                'failed': failed_count,
                'duration': 'N/A'
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': 'Test timed out after 60 seconds',
                'test_count': 0,
                'passed': 0,
                'failed': 1,
                'duration': '60+'
            }
        except Exception as e:
            return {
                'success': False,
                'output': f'Exception: {str(e)}',
                'test_count': 0,
                'passed': 0,
                'failed': 1,
                'duration': 'N/A'
            }
    
    def run_test_file(self, test_info):
        """Run a single test file based on its framework"""
        start_time = datetime.now()
        
        if test_info['framework'] == 'pytest':
            result = self.run_pytest_file(test_info)
        else:
            result = self.run_unittest_file(test_info)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        result['duration'] = f"{duration:.2f}s"
        
        # Store result
        self.test_results[test_info['file']] = {
            'test_info': test_info,
            'result': result,
            'timestamp': end_time.isoformat()
        }
        
        # Track pass/fail
        if result['success']:
            self.passed_tests.append(test_info['file'])
            status = "✅ PASS"
        else:
            self.failed_tests.append(test_info['file'])
            status = "❌ FAIL"
        
        logger.info(f"{status} - {test_info['file']} ({result['duration']})")
        
        return result['success']
    
    def run_category_tests(self, category, max_tests_per_category=5):
        """Run tests for a specific category"""
        if category not in self.test_categories:
            logger.warning(f"No tests found for category: {category}")
            return 0, 0
        
        tests = self.test_categories[category][:max_tests_per_category]  # Limit tests per category
        
        logger.info(f"\n{'='*60}")
        logger.info(f"TESTING CATEGORY: {category.upper()}")
        logger.info(f"Running {len(tests)} tests")
        logger.info(f"{'='*60}")
        
        passed = 0
        total = len(tests)
        
        for test_info in tests:
            if self.run_test_file(test_info):
                passed += 1
        
        logger.info(f"Category {category}: {passed}/{total} tests passed")
        return passed, total
    
    def run_all_tests(self, max_tests_per_category=3):
        """Run all discovered tests by category"""
        logger.info("🚀 Starting comprehensive test run...")
        
        start_time = datetime.now()
        
        # Discover tests first
        categories = self.discover_test_files()
        
        if not categories:
            logger.error("No test files found!")
            return False
        
        logger.info(f"Found tests in {len(categories)} categories:")
        for category, tests in categories.items():
            logger.info(f"  {category}: {len(tests)} tests")
        
        # Run tests by category
        total_passed = 0
        total_tests = 0
        
        # Priority order for categories
        priority_categories = [
            'database', 'authentication', 'booking', 'chatbot', 
            'routes', 'qr_codes', 'payment', 'notifications', 
            'realtime', 'admin', 'general'
        ]
        
        # Run priority categories first
        for category in priority_categories:
            if category in categories:
                passed, total = self.run_category_tests(category, max_tests_per_category)
                total_passed += passed
                total_tests += total
        
        # Run remaining categories
        for category in categories:
            if category not in priority_categories:
                passed, total = self.run_category_tests(category, max_tests_per_category)
                total_passed += passed
                total_tests += total
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Generate comprehensive report
        self.generate_comprehensive_report(total_passed, total_tests, duration)
        
        return total_passed == total_tests
    
    def generate_comprehensive_report(self, total_passed, total_tests, duration):
        """Generate comprehensive test report"""
        
        # Calculate statistics
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Categorize results
        category_stats = {}
        for category, tests in self.test_categories.items():
            category_passed = 0
            category_total = 0
            
            for test_info in tests:
                file_path = test_info['file']
                if file_path in self.test_results:
                    category_total += 1
                    if self.test_results[file_path]['result']['success']:
                        category_passed += 1
            
            if category_total > 0:
                category_stats[category] = {
                    'passed': category_passed,
                    'total': category_total,
                    'success_rate': (category_passed / category_total * 100)
                }
        
        # Create detailed report
        report = {
            'summary': {
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': duration,
                'total_tests': total_tests,
                'passed_tests': total_passed,
                'failed_tests': total_tests - total_passed,
                'success_rate': success_rate
            },
            'category_stats': category_stats,
            'test_categories': {k: len(v) for k, v in self.test_categories.items()},
            'detailed_results': self.test_results,
            'failed_tests': self.failed_tests,
            'passed_tests': self.passed_tests
        }
        
        # Save report
        with open('comprehensive_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        logger.info(f"\n{'='*70}")
        logger.info("COMPREHENSIVE TEST RESULTS SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Total Tests Run: {total_tests}")
        logger.info(f"Tests Passed: {total_passed}")
        logger.info(f"Tests Failed: {total_tests - total_passed}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Duration: {duration:.2f} seconds")
        
        logger.info(f"\n📊 RESULTS BY CATEGORY:")
        for category, stats in category_stats.items():
            logger.info(f"  {category.title()}: {stats['passed']}/{stats['total']} ({stats['success_rate']:.1f}%)")
        
        if self.failed_tests:
            logger.info(f"\n❌ FAILED TESTS:")
            for i, test in enumerate(self.failed_tests, 1):
                logger.info(f"   {i}. {test}")
        
        logger.info(f"\n📄 Detailed report saved to: comprehensive_test_report.json")
        
        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        if success_rate < 50:
            logger.info("   1. Critical issues detected - run diagnostics and fixes first")
        elif success_rate < 80:
            logger.info("   1. Some tests failing - review failed tests and fix issues")
        else:
            logger.info("   1. System is in good condition!")
        
        if 'database' in category_stats and category_stats['database']['success_rate'] < 80:
            logger.info("   2. Database issues detected - check Supabase connection")
        
        if 'chatbot' in category_stats and category_stats['chatbot']['success_rate'] < 80:
            logger.info("   3. Chatbot issues detected - check API keys and imports")
        
        return report

def main():
    """Main execution"""
    runner = CricVerseTestRunner()
    
    # Check if we should run limited tests
    max_tests = 3
    if len(sys.argv) > 1:
        try:
            max_tests = int(sys.argv[1])
        except ValueError:
            logger.warning("Invalid max_tests argument, using default of 3")
    
    logger.info(f"Running up to {max_tests} tests per category")
    
    success = runner.run_all_tests(max_tests_per_category=max_tests)
    
    if success:
        logger.info("🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.warning("⚠️ Some tests failed - check the report for details")
        sys.exit(1)

if __name__ == "__main__":
    main()
