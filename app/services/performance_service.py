"""
Performance Optimization Service for CricVerse
Comprehensive performance enhancements including caching, database optimization, and loading time improvements
Big Bash League Cricket Platform
"""

import os
import time
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
from flask import request, g, current_app
from flask_caching import Cache
import redis
from sqlalchemy import text
from app import db

# Configure logging
logger = logging.getLogger(__name__)

class CacheManager:
    """Advanced caching manager with multiple cache strategies"""
    
    def __init__(self):
        self.cache = None
        self.redis_client = None
        self._initialize_cache()
    
    def _initialize_cache(self):
        """Initialize cache systems"""
        try:
            # Initialize Flask-Caching
            cache_config = {
                'CACHE_TYPE': 'redis' if os.getenv('REDIS_URL') else 'simple',
                'CACHE_DEFAULT_TIMEOUT': 300,
                'CACHE_KEY_PREFIX': 'cricverse_'
            }
            
            if os.getenv('REDIS_URL'):
                cache_config['CACHE_REDIS_URL'] = os.getenv('REDIS_URL')
            
            self.cache = Cache()
            
            # Initialize Redis client for advanced operations
            if os.getenv('REDIS_URL'):
                self.redis_client = redis.from_url(os.getenv('REDIS_URL'))
                
        except Exception as e:
            logger.error(f"Cache initialization failed: {e}")
            # Fallback to simple in-memory cache
            self.cache = Cache(config={'CACHE_TYPE': 'simple'})
    
    def cached(self, timeout: int = 300, key_prefix: str = None):
        """Decorator for caching function results"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_cache_key(f.__name__, args, kwargs, key_prefix)
                
                # Try to get from cache
                try:
                    cached_result = self.cache.get(cache_key)
                    if cached_result is not None:
                        logger.debug(f"Cache hit for key: {cache_key}")
                        return cached_result
                except Exception as e:
                    logger.warning(f"Cache get failed: {e}")
                
                # Execute function and cache result
                result = f(*args, **kwargs)
                
                try:
                    self.cache.set(cache_key, result, timeout=timeout)
                    logger.debug(f"Cached result for key: {cache_key}")
                except Exception as e:
                    logger.warning(f"Cache set failed: {e}")
                
                return result
            return decorated_function
        return decorator
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache keys matching pattern"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(f"cricverse_{pattern}*")
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} cache keys matching pattern: {pattern}")
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                return {
                    'type': 'redis',
                    'used_memory': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'hit_rate': self._calculate_hit_rate(info.get('keyspace_hits', 0), info.get('keyspace_misses', 0))
                }
            else:
                return {'type': 'simple', 'status': 'active'}
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'type': 'unknown', 'error': str(e)}
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict, prefix: str = None) -> str:
        """Generate unique cache key"""
        key_parts = [func_name]
        
        if prefix:
            key_parts.insert(0, prefix)
        
        # Add args and kwargs to key
        if args:
            key_parts.extend([str(arg) for arg in args])
        
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
        
        key_string = "_".join(key_parts)
        
        # Hash long keys
        if len(key_string) > 200:
            key_string = hashlib.md5(key_string.encode()).hexdigest()
        
        return key_string
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

class DatabaseOptimizer:
    """Database query optimization and monitoring"""
    
    def __init__(self):
        self.slow_queries = []
        self.query_stats = {}
    
    def monitor_query_performance(self, f):
        """Decorator to monitor database query performance"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log slow queries
                if execution_time > 1.0:  # Queries taking more than 1 second
                    self.slow_queries.append({
                        'function': f.__name__,
                        'execution_time': execution_time,
                        'timestamp': datetime.utcnow(),
                        'args': str(args)[:200],  # Truncate long args
                        'kwargs': str(kwargs)[:200]
                    })
                    logger.warning(f"Slow query detected: {f.__name__} took {execution_time:.2f}s")
                
                # Update query statistics
                if f.__name__ not in self.query_stats:
                    self.query_stats[f.__name__] = {
                        'count': 0,
                        'total_time': 0,
                        'avg_time': 0,
                        'max_time': 0
                    }
                
                stats = self.query_stats[f.__name__]
                stats['count'] += 1
                stats['total_time'] += execution_time
                stats['avg_time'] = stats['total_time'] / stats['count']
                stats['max_time'] = max(stats['max_time'], execution_time)
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Query failed after {execution_time:.2f}s: {f.__name__} - {str(e)}")
                raise
        
        return decorated_function
    
    def optimize_database_connections(self):
        """Optimize database connection pool"""
        try:
            # Get current connection pool info
            engine = db.engine
            pool = engine.pool
            
            pool_info = {
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            }
            
            logger.info(f"Database pool status: {pool_info}")
            
            # Optimize based on usage patterns
            if pool_info['checked_out'] > pool_info['pool_size'] * 0.8:
                logger.warning("Database pool utilization high, consider increasing pool size")
            
            return pool_info
            
        except Exception as e:
            logger.error(f"Failed to optimize database connections: {e}")
            return {}
    
    def analyze_query_patterns(self) -> Dict[str, Any]:
        """Analyze query patterns and suggest optimizations"""
        analysis = {
            'slow_queries_count': len(self.slow_queries),
            'most_frequent_queries': [],
            'slowest_queries': [],
            'optimization_suggestions': []
        }
        
        # Find most frequent queries
        if self.query_stats:
            sorted_by_count = sorted(self.query_stats.items(), key=lambda x: x[1]['count'], reverse=True)
            analysis['most_frequent_queries'] = [
                {
                    'function': func,
                    'count': stats['count'],
                    'avg_time': round(stats['avg_time'], 3)
                }
                for func, stats in sorted_by_count[:10]
            ]
        
        # Find slowest queries
        if self.slow_queries:
            sorted_by_time = sorted(self.slow_queries, key=lambda x: x['execution_time'], reverse=True)
            analysis['slowest_queries'] = sorted_by_time[:10]
        
        # Generate optimization suggestions
        analysis['optimization_suggestions'] = self._generate_optimization_suggestions()
        
        return analysis
    
    def _generate_optimization_suggestions(self) -> List[str]:
        """Generate database optimization suggestions"""
        suggestions = []
        
        # Check for frequent slow queries
        frequent_slow = {}
        for query in self.slow_queries:
            func_name = query['function']
            frequent_slow[func_name] = frequent_slow.get(func_name, 0) + 1
        
        for func_name, count in frequent_slow.items():
            if count > 5:
                suggestions.append(f"Consider optimizing {func_name} - appears {count} times in slow queries")
        
        # Check query statistics
        for func_name, stats in self.query_stats.items():
            if stats['avg_time'] > 0.5:
                suggestions.append(f"Consider adding indexes for {func_name} - average time {stats['avg_time']:.2f}s")
            
            if stats['count'] > 100 and stats['avg_time'] > 0.1:
                suggestions.append(f"Consider caching results for {func_name} - called {stats['count']} times")
        
        return suggestions

class PerformanceMonitor:
    """Real-time performance monitoring"""
    
    def __init__(self):
        self.request_times = []
        self.endpoint_stats = {}
        self.resource_usage = {}
    
    def monitor_request_performance(self, f):
        """Decorator to monitor request performance"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            try:
                result = f(*args, **kwargs)
                
                execution_time = time.time() - start_time
                memory_used = self._get_memory_usage() - start_memory
                
                # Record performance metrics
                endpoint = request.endpoint or f.__name__
                
                if endpoint not in self.endpoint_stats:
                    self.endpoint_stats[endpoint] = {
                        'count': 0,
                        'total_time': 0,
                        'avg_time': 0,
                        'max_time': 0,
                        'min_time': float('inf'),
                        'total_memory': 0,
                        'avg_memory': 0
                    }
                
                stats = self.endpoint_stats[endpoint]
                stats['count'] += 1
                stats['total_time'] += execution_time
                stats['avg_time'] = stats['total_time'] / stats['count']
                stats['max_time'] = max(stats['max_time'], execution_time)
                stats['min_time'] = min(stats['min_time'], execution_time)
                stats['total_memory'] += memory_used
                stats['avg_memory'] = stats['total_memory'] / stats['count']
                
                # Log slow requests
                if execution_time > 2.0:
                    logger.warning(f"Slow request: {endpoint} took {execution_time:.2f}s")
                
                # Store recent request times
                self.request_times.append({
                    'endpoint': endpoint,
                    'time': execution_time,
                    'memory': memory_used,
                    'timestamp': datetime.utcnow()
                })
                
                # Keep only recent requests (last 1000)
                if len(self.request_times) > 1000:
                    self.request_times = self.request_times[-1000:]
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Request failed after {execution_time:.2f}s: {endpoint} - {str(e)}")
                raise
        
        return decorated_function
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        now = datetime.utcnow()
        recent_requests = [
            req for req in self.request_times
            if (now - req['timestamp']).total_seconds() < 3600  # Last hour
        ]
        
        report = {
            'summary': {
                'total_requests': len(recent_requests),
                'avg_response_time': 0,
                'slowest_endpoint': None,
                'fastest_endpoint': None,
                'total_endpoints': len(self.endpoint_stats)
            },
            'endpoint_performance': [],
            'slow_requests': [],
            'recommendations': []
        }
        
        if recent_requests:
            # Calculate summary statistics
            total_time = sum(req['time'] for req in recent_requests)
            report['summary']['avg_response_time'] = total_time / len(recent_requests)
            
            # Find slow requests
            slow_requests = [req for req in recent_requests if req['time'] > 1.0]
            report['slow_requests'] = sorted(slow_requests, key=lambda x: x['time'], reverse=True)[:10]
        
        # Endpoint performance
        if self.endpoint_stats:
            sorted_endpoints = sorted(
                self.endpoint_stats.items(),
                key=lambda x: x[1]['avg_time'],
                reverse=True
            )
            
            report['endpoint_performance'] = [
                {
                    'endpoint': endpoint,
                    'count': stats['count'],
                    'avg_time': round(stats['avg_time'], 3),
                    'max_time': round(stats['max_time'], 3),
                    'min_time': round(stats['min_time'], 3),
                    'avg_memory': round(stats['avg_memory'], 2)
                }
                for endpoint, stats in sorted_endpoints[:20]
            ]
            
            # Find slowest and fastest endpoints
            if sorted_endpoints:
                report['summary']['slowest_endpoint'] = sorted_endpoints[0][0]
                report['summary']['fastest_endpoint'] = sorted_endpoints[-1][0]
        
        # Generate recommendations
        report['recommendations'] = self._generate_performance_recommendations()
        
        return report
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage (simplified)"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0
    
    def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Check for slow endpoints
        for endpoint, stats in self.endpoint_stats.items():
            if stats['avg_time'] > 1.0:
                recommendations.append(f"Optimize {endpoint} - average response time {stats['avg_time']:.2f}s")
            
            if stats['count'] > 50 and stats['avg_time'] > 0.5:
                recommendations.append(f"Consider caching for {endpoint} - frequently accessed with {stats['avg_time']:.2f}s response time")
        
        # Check overall performance
        if self.request_times:
            recent_avg = sum(req['time'] for req in self.request_times[-100:]) / min(100, len(self.request_times))
            if recent_avg > 0.5:
                recommendations.append("Overall response time is high - consider database optimization and caching")
        
        return recommendations

class PerformanceService:
    """Main performance optimization service"""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.db_optimizer = DatabaseOptimizer()
        self.performance_monitor = PerformanceMonitor()
    
    def init_app(self, app):
        """Initialize performance service with Flask app"""
        try:
            # Initialize cache with app
            if self.cache_manager.cache:
                self.cache_manager.cache.init_app(app)
            
            # Add performance monitoring middleware
            @app.before_request
            def before_request():
                g.start_time = time.time()
            
            @app.after_request
            def after_request(response):
                # Add performance headers
                if hasattr(g, 'start_time'):
                    response_time = time.time() - g.start_time
                    response.headers['X-Response-Time'] = f"{response_time:.3f}s"
                
                # Add cache headers for static content
                if request.endpoint and 'static' in request.endpoint:
                    response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
                
                return response
            
            logger.info("Performance service initialized successfully")
            
        except Exception as e:
            logger.error(f"Performance service initialization failed: {e}")
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'cache_stats': self.cache_manager.get_cache_stats(),
            'database_analysis': self.db_optimizer.analyze_query_patterns(),
            'performance_report': self.performance_monitor.get_performance_report(),
            'system_recommendations': self._generate_system_recommendations()
        }
    
    def optimize_for_event(self, event_id: int):
        """Pre-optimize system for high-traffic event"""
        try:
            # Pre-cache event data
            from app.services.enhanced_booking_service import enhanced_booking_service
            
            # Cache seat availability
            availability = enhanced_booking_service.get_seat_availability(event_id)
            cache_key = f"seat_availability_{event_id}"
            self.cache_manager.cache.set(cache_key, availability, timeout=300)
            
            # Cache parking availability
            parking = enhanced_booking_service.get_parking_availability(event_id)
            cache_key = f"parking_availability_{event_id}"
            self.cache_manager.cache.set(cache_key, parking, timeout=300)
            
            logger.info(f"Pre-cached data for event {event_id}")
            
        except Exception as e:
            logger.error(f"Event optimization failed: {e}")
    
    def clear_cache_for_booking(self, event_id: int):
        """Clear relevant caches after booking"""
        try:
            patterns_to_clear = [
                f"seat_availability_{event_id}",
                f"parking_availability_{event_id}",
                f"event_stats_{event_id}",
                "dashboard_stats",
                "analytics_"
            ]
            
            for pattern in patterns_to_clear:
                self.cache_manager.invalidate_pattern(pattern)
            
            logger.info(f"Cleared caches for event {event_id}")
            
        except Exception as e:
            logger.error(f"Cache clearing failed: {e}")
    
    def _generate_system_recommendations(self) -> List[str]:
        """Generate system-wide performance recommendations"""
        recommendations = []
        
        # Check cache performance
        cache_stats = self.cache_manager.get_cache_stats()
        if cache_stats.get('hit_rate', 0) < 70:
            recommendations.append("Cache hit rate is low - consider increasing cache timeout or improving cache keys")
        
        # Check database performance
        db_analysis = self.db_optimizer.analyze_query_patterns()
        if db_analysis['slow_queries_count'] > 10:
            recommendations.append("High number of slow queries detected - database optimization needed")
        
        # Check overall system performance
        perf_report = self.performance_monitor.get_performance_report()
        if perf_report['summary']['avg_response_time'] > 1.0:
            recommendations.append("Average response time is high - consider scaling or optimization")
        
        return recommendations

# Create global performance service instance
performance_service = PerformanceService()