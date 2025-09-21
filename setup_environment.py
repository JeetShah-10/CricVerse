"""
Environment Setup Script for CricVerse Stadium System
Helps set up environment variables from cricverse.env file
"""

import os
import sys
from pathlib import Path

def load_env_file(env_file_path: str = "cricverse.env") -> bool:
    """Load environment variables from cricverse.env file"""
    try:
        if not os.path.exists(env_file_path):
            print(f"❌ Environment file {env_file_path} not found!")
            print("Please ensure cricverse.env exists with your Supabase configuration.")
            return False
        
        print(f"📄 Loading environment variables from {env_file_path}")
        
        with open(env_file_path, 'r') as f:
            lines = f.readlines()
        
        loaded_vars = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                os.environ[key] = value
                loaded_vars.append(key)
        
        print(f"✅ Loaded {len(loaded_vars)} environment variables:")
        for var in loaded_vars:
            # Don't print sensitive values
            if 'KEY' in var or 'SECRET' in var or 'PASSWORD' in var:
                print(f"   - {var}: ***hidden***")
            else:
                print(f"   - {var}: {os.environ[var]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading environment file: {str(e)}")
        return False

def verify_required_vars() -> bool:
    """Verify that all required environment variables are set"""
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    present_vars = []
    
    for var in required_vars:
        if os.getenv(var):
            present_vars.append(var)
        else:
            missing_vars.append(var)
    
    print(f"\n🔍 Environment Variables Check:")
    print(f"   Present: {len(present_vars)}/{len(required_vars)}")
    
    for var in present_vars:
        print(f"   ✅ {var}")
    
    for var in missing_vars:
        print(f"   ❌ {var} - MISSING")
    
    if missing_vars:
        print(f"\n⚠️ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please add these to your cricverse.env file.")
        return False
    
    print("\n✅ All required environment variables are present!")
    return True

def main():
    """Main setup function"""
    print("🏏 CricVerse Stadium System - Environment Setup")
    print("=" * 50)
    
    # Load environment file
    if not load_env_file():
        return 1
    
    # Verify required variables
    if not verify_required_vars():
        return 1
    
    print("\n🎉 Environment setup complete!")
    print("You can now run the system tests: python test_cricverse_system.py")
    return 0

if __name__ == "__main__":
    exit(main())
