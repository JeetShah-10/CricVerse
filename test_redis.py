import os
import redis

# Get Redis URL from environment
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
print(f"Testing Redis connection to: {redis_url}")

try:
    # Create Redis client
    r = redis.from_url(redis_url, decode_responses=True)
    
    # Test connection
    r.ping()
    print("✅ Redis connection successful")
    
    # Test setting and getting a value
    r.set('test_key', 'test_value')
    value = r.get('test_key')
    print(f"✅ Redis set/get test: {value}")
    
except Exception as e:
    print(f"❌ Redis connection failed: {e}")