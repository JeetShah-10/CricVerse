#!/usr/bin/env python3
"""
Update .env file for Supabase configuration
This script will update your .env file to use Supabase instead of SQLite.
"""

import os
import re
from pathlib import Path

def update_env_file():
    """Update .env file with Supabase configuration"""
    env_file = Path('c:\\Users\\shahj\\OneDrive\\Desktop\\Stadium System\\.env')
    
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    # Read current content
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Update DATABASE_URL to use Supabase
    # Note: You'll need to replace YOUR_ACTUAL_PASSWORD with your real database password
    supabase_db_url = 'postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.tiyokcstdmlhpswurelh.supabase.co:5432/postgres'
    
    # Replace the DATABASE_URL line
    content = re.sub(
        r'DATABASE_URL=sqlite:///cricverse\.db',
        f'DATABASE_URL={supabase_db_url}',
        content
    )
    
    # Add Supabase configuration if not present
    if 'SUPABASE_URL' not in content:
        supabase_config = '''
# Supabase Configuration
SUPABASE_URL=https://tiyokcstdmlhpswurelh.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRpeW9rY3N0ZG1saHBzd3VyZWxoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc2OTkxOTMsImV4cCI6MjA3MzI3NTE5M30.60sud90R8o7elSLmt7AuYK7lYb_F8mIKp04UsCfa0Lo
'''
        # Add before the security section
        content = content.replace(
            '# Security',
            f'{supabase_config}\n# Security'
        )
    
    # Write updated content
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ .env file updated with Supabase configuration!")
    print("📝 Note: You still need to replace 'YOUR_ACTUAL_PASSWORD' with your real database password")
    return True

if __name__ == "__main__":
    print("🔧 Updating .env file for Supabase configuration...")
    print("=" * 50)
    
    if update_env_file():
        print("\n✅ .env file updated successfully!")
        print("\n📋 Next steps:")
        print("1. Open your .env file")
        print("2. Replace 'YOUR_ACTUAL_PASSWORD' with your real database password")
        print("3. Run the test_supabase_connection.py script to verify")
    else:
        print("\n❌ Failed to update .env file!")