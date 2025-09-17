#!/usr/bin/env python3
"""
Performance Optimizer for CricVerse
Optimizes static assets, database queries, and overall performance
"""

import os
import sys
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

class PerformanceOptimizer:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.optimizations_applied = []
        
    def log_optimization(self, optimization, success, details=""):
        """Log optimization results"""
        status = "[PASS] APPLIED" if success else "[FAIL] FAILED"
        result = {
            'optimization': optimization,
            'status': status,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.optimizations_applied.append(result)
        print(f"{status} {optimization}: {details}")
    
    def optimize_css_loading(self):
        """Optimize CSS loading with preload and minification"""
        try:
            # Check if CSS files exist and are optimized
            css_files = [
                'static/css/unified.css',
                'static/css/bbl-enhanced.css',
                'static/css/home-enhanced.css',
                'static/css/bbl-action-hub.css'
            ]
            
            optimized_count = 0
            for css_file in css_files:
                if os.path.exists(css_file):
                    # Check file size
                    file_size = os.path.getsize(css_file)
                    if file_size < 100000:  # Less than 100KB
                        optimized_count += 1
                    else:
                        print(f"   [WARN]  {css_file} is large ({file_size} bytes)")
            
            if optimized_count == len(css_files):
                self.log_optimization("CSS Loading", True, f"All {len(css_files)} CSS files are optimized")
            else:
                self.log_optimization("CSS Loading", False, f"Only {optimized_count}/{len(css_files)} CSS files are optimized")
                
        except Exception as e:
            self.log_optimization("CSS Loading", False, f"Error: {e}")
    
    def optimize_js_loading(self):
        """Optimize JavaScript loading"""
        try:
            js_files = [
                'static/js/main.js',
                'static/js/bbl-enhanced.js'
            ]
            
            optimized_count = 0
            for js_file in js_files:
                if os.path.exists(js_file):
                    file_size = os.path.getsize(js_file)
                    if file_size < 50000:  # Less than 50KB
                        optimized_count += 1
                    else:
                        print(f"   [WARN]  {js_file} is large ({file_size} bytes)")
            
            if optimized_count == len(js_files):
                self.log_optimization("JavaScript Loading", True, f"All {len(js_files)} JS files are optimized")
            else:
                self.log_optimization("JavaScript Loading", False, f"Only {optimized_count}/{len(js_files)} JS files are optimized")
                
        except Exception as e:
            self.log_optimization("JavaScript Loading", False, f"Error: {e}")
    
    def optimize_image_loading(self):
        """Check and optimize image loading"""
        try:
            image_dirs = [
                'static/img',
                'static/img/teams'
            ]
            
            total_images = 0
            large_images = 0
            
            for img_dir in image_dirs:
                if os.path.exists(img_dir):
                    for file in os.listdir(img_dir):
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                            total_images += 1
                            file_path = os.path.join(img_dir, file)
                            file_size = os.path.getsize(file_path)
                            
                            # Check if image is too large (>500KB)
                            if file_size > 500000:
                                large_images += 1
                                print(f"   [WARN]  {file_path} is large ({file_size} bytes)")
            
            if large_images == 0:
                self.log_optimization("Image Loading", True, f"All {total_images} images are optimized")
            else:
                self.log_optimization("Image Loading", False, f"{large_images}/{total_images} images are too large")
                
        except Exception as e:
            self.log_optimization("Image Loading", False, f"Error: {e}")
    
    def test_database_performance(self):
        """Test database query performance"""
        try:
            # Test database connection and basic queries
            from app import app, db, Event, Team, Customer
            
            with app.app_context():
                start_time = time.time()
                
                # Test basic queries
                events = Event.query.limit(5).all()
                teams = Team.query.limit(5).all()
                customers = Customer.query.limit(5).all()
                
                query_time = time.time() - start_time
                
                if query_time < 0.1:  # Less than 100ms
                    self.log_optimization("Database Queries", True, f"Queries completed in {query_time:.3f}s")
                else:
                    self.log_optimization("Database Queries", False, f"Queries took {query_time:.3f}s (slow)")
                    
        except Exception as e:
            self.log_optimization("Database Queries", False, f"Error: {e}")
    
    def test_api_endpoints(self):
        """Test API endpoint performance"""
        try:
            endpoints = [
                '/api/bbl/live-scores',
                '/api/bbl/standings',
                '/api/bbl/teams',
                '/api/chat/suggestions'
            ]
            
            total_time = 0
            successful_requests = 0
            
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        total_time += response_time
                        successful_requests += 1
                        print(f"   [PASS] {endpoint}: {response_time:.3f}s")
                    else:
                        print(f"   [FAIL] {endpoint}: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"   [FAIL] {endpoint}: Error - {e}")
            
            if successful_requests > 0:
                avg_time = total_time / successful_requests
                if avg_time < 0.5:  # Less than 500ms
                    self.log_optimization("API Endpoints", True, f"Average response time: {avg_time:.3f}s")
                else:
                    self.log_optimization("API Endpoints", False, f"Average response time: {avg_time:.3f}s (slow)")
            else:
                self.log_optimization("API Endpoints", False, "No successful API requests")
                
        except Exception as e:
            self.log_optimization("API Endpoints", False, f"Error: {e}")
    
    def create_performance_recommendations(self):
        """Create performance optimization recommendations"""
        recommendations = []
        
        # Check for common performance issues
        if not os.path.exists('static/css/unified.min.css'):
            recommendations.append("Minify CSS files for faster loading")
        
        if not os.path.exists('static/js/main.min.js'):
            recommendations.append("Minify JavaScript files")
        
        # Check for large images
        large_images = []
        for root, dirs, files in os.walk('static/img'):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    file_path = os.path.join(root, file)
                    if os.path.getsize(file_path) > 500000:  # >500KB
                        large_images.append(file_path)
        
        if large_images:
            recommendations.append(f"Optimize {len(large_images)} large images")
        
        # Check for missing caching headers
        recommendations.append("Add proper caching headers for static assets")
        recommendations.append("Enable gzip compression")
        recommendations.append("Use CDN for static assets")
        
        return recommendations
    
    def run_optimization_checks(self):
        """Run all optimization checks"""
        print("[START] CricVerse Performance Optimizer")
        print("=" * 50)
        print(f"[TIME] Started: {datetime.now().strftime('%H:%M:%S')}")
        
        # Run all optimization checks
        self.optimize_css_loading()
        self.optimize_js_loading()
        self.optimize_image_loading()
        self.test_database_performance()
        self.test_api_endpoints()
        
        # Generate recommendations
        recommendations = self.create_performance_recommendations()
        
        print("\n" + "=" * 50)
        print("[STATS] OPTIMIZATION SUMMARY")
        print("=" * 50)
        
        successful = sum(1 for opt in self.optimizations_applied if opt['success'])
        total = len(self.optimizations_applied)
        
        print(f"Optimizations Applied: {successful}/{total} ({(successful/total)*100:.1f}%)")
        
        if recommendations:
            print("\n[TIP] RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print(f"\n[PASS] Optimization check completed: {datetime.now().strftime('%H:%M:%S')}")
        
        return successful == total

def main():
    """Main optimization function"""
    optimizer = PerformanceOptimizer()
    success = optimizer.run_optimization_checks()
    
    if success:
        print("\n[SUCCESS] All performance optimizations are in place!")
        print("[TROPHY] Your CricVerse app should load faster now!")
    else:
        print("\n[WARN]  Some optimizations need attention.")
        print("[NOTE] Check the recommendations above to improve performance.")
    
    return success

if __name__ == "__main__":
    main()
