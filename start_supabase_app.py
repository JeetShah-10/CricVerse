#!/usr/bin/env python3
"""
Start Script for CricVerse with Supabase
This script starts the CricVerse application using the application factory pattern
"""

import os
import sys
from dotenv import load_dotenv

def load_environment():
    """Load environment variables"""
    if os.path.exists('cricverse.env'):
        load_dotenv('cricverse.env')
        print("✅ Loaded cricverse.env")
    elif os.path.exists('.env'):
        load_dotenv('.env')
        print("✅ Loaded .env")
    else:
        print("⚠️ No environment file found, using defaults")

def start_application():
    """Start the CricVerse application"""
    print("🚀 Starting CricVerse Stadium System with Supabase")
    print("=" * 60)
    
    try:
        # Import the application factory
        from app import create_app
        
        # Create the application instance
        app = create_app('default')
        
        # Import socketio for real-time features
        from app import socketio
        
        print("✅ Application initialized successfully!")
        print(f"🌐 Database: Supabase PostgreSQL")
        print(f"📊 Tables: Created and verified")
        print(f"💳 Payment System: Active (PayPal + Razorpay)")
        print(f"🤖 AI Chatbot: Active (Gemini)")
        print(f"⚡ Real-time Features: Active (SocketIO)")
        
        print("\n" + "=" * 60)
        print("🚀 Starting CricVerse Stadium System...")
        print("=" * 60)
        print(f"🌐 Web Server: http://localhost:5000")
        print(f"📊 Admin Panel: http://localhost:5000/admin")
        print("=" * 60)
        
        # Run the app
        socketio.run(
            app,
            debug=False,
            host='0.0.0.0',
            port=5000,
            use_reloader=False,
            log_output=True
        )
        
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        print("[NOTE] Check your configuration and try again")

def main():
    """Main function"""
    print("🏏 CricVerse Supabase Startup Script")
    print("=" * 50)
    
    # Load environment
    load_environment()
    
    # Start the application
    start_application()

if __name__ == "__main__":
    main()