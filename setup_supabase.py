#!/usr/bin/env python3
"""
Interactive Supabase Configuration Setup for CricVerse
This script will help you configure your Supabase connection properly.
"""

import os
import re
import sys
from pathlib import Path

def get_supabase_info():
    """Interactive function to get Supabase configuration"""
    print("🏏 CricVerse Supabase Configuration Setup")
    print("=" * 50)
    print()
    print("You need to get the following from your Supabase dashboard:")
    print("1. Go to https://supabase.com/dashboard/projects")
    print("2. Select your project (or create a new one)")
    print("3. Go to Settings > Database")
    print("4. Copy the Connection string")
    print("5. Go to Settings > API to get your API keys")
    print()
    
    # Get project reference
    print("📍 Step 1: Project Reference")
    project_ref = input("Enter your Supabase project reference (e.g., 'abcdefghijklmnop'): ").strip()
    
    if not project_ref:
        print("❌ Project reference is required!")
        return None
        
    # Get database password
    print("\n🔐 Step 2: Database Password")
    db_password = input("Enter your database password: ").strip()
    
    if not db_password:
        print("❌ Database password is required!")
        return None
    
    # Get API keys
    print("\n🔑 Step 3: API Keys")
    anon_key = input("Enter your Supabase anon/public key: ").strip()
    service_key = input("Enter your Supabase service role key (optional): ").strip()
    
    if not anon_key:
        print("❌ Anon key is required!")
        return None
    
    return {
        'project_ref': project_ref,
        'db_password': db_password,
        'anon_key': anon_key,
        'service_key': service_key or 'your-actual-supabase-service-role-key'
    }

def update_env_file(config):
    """Update the cricverse.env file with actual Supabase values"""
    env_file = Path('cricverse.env')
    
    if not env_file.exists():
        print("❌ cricverse.env file not found!")
        return False
    
    # Read current content
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Replace placeholders
    database_url = f"postgresql://postgres:{config['db_password']}@db.{config['project_ref']}.supabase.co:5432/postgres"
    supabase_url = f"https://{config['project_ref']}.supabase.co"
    
    # Update DATABASE_URL
    content = re.sub(
        r'DATABASE_URL=postgresql://postgres:\[YOUR_DB_PASSWORD\]@db\.\[YOUR_PROJECT_REF\]\.supabase\.co:5432/postgres',
        f'DATABASE_URL={database_url}',
        content
    )
    
    # Update SUPABASE_URL
    content = re.sub(
        r'SUPABASE_URL=https://\[YOUR_PROJECT_REF\]\.supabase\.co',
        f'SUPABASE_URL={supabase_url}',
        content
    )
    
    # Update SUPABASE_KEY
    content = re.sub(
        r'SUPABASE_KEY=your-actual-supabase-anon-key',
        f'SUPABASE_KEY={config["anon_key"]}',
        content
    )
    
    # Update SUPABASE_SERVICE_ROLE_KEY
    if config['service_key'] != 'your-actual-supabase-service-role-key':
        content = re.sub(
            r'SUPABASE_SERVICE_ROLE_KEY=your-actual-supabase-service-role-key',
            f'SUPABASE_SERVICE_ROLE_KEY={config["service_key"]}',
            content
        )
    
    # Write updated content
    with open(env_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {env_file} with your Supabase configuration!")
    return True

def test_connection(config):
    """Test the Supabase connection"""
    print("\n🧪 Testing Supabase connection...")
    
    try:
        # Set environment variables temporarily
        os.environ['DATABASE_URL'] = f"postgresql://postgres:{config['db_password']}@db.{config['project_ref']}.supabase.co:5432/postgres"
        os.environ['SUPABASE_URL'] = f"https://{config['project_ref']}.supabase.co"
        os.environ['SUPABASE_KEY'] = config['anon_key']
        
        # Test connection using our supabase_config module
        from supabase_config import SupabaseConfig
        
        supabase_config = SupabaseConfig()
        
        if supabase_config.test_connection():
            print("✅ Supabase connection successful!")
            return True
        else:
            print("❌ Supabase connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("Starting Supabase configuration setup...\n")
    
    # Check if we're in the right directory
    if not Path('cricverse.env').exists():
        print("❌ Please run this script from the Stadium System directory!")
        sys.exit(1)
    
    try:
        # Get Supabase configuration
        config = get_supabase_info()
        if not config:
            print("❌ Configuration setup failed!")
            sys.exit(1)
        
        # Update environment file
        if not update_env_file(config):
            print("❌ Failed to update environment file!")
            sys.exit(1)
        
        # Test connection
        if test_connection(config):
            print("\n🎉 Supabase configuration completed successfully!")
            print("You can now run your Flask application with:")
            print("   python app.py")
        else:
            print("\n⚠️  Configuration saved but connection test failed.")
            print("Please double-check your Supabase credentials.")
            
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()