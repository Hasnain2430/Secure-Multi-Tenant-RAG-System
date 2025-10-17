#!/usr/bin/env python3
"""
Web Interface Startup Script for Secure Multi-Tenant RAG System
Beautiful, modern frontend with real-time chat interface
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    try:
        import flask
        import flask_socketio
        print("Flask dependencies found")
        return True
    except ImportError as e:
        print(f"Missing dependencies: {e}")
        print("Installing web dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("Failed to install dependencies")
            return False

def check_config():
    """Check if config.yaml exists and has API key"""
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("config.yaml not found!")
        print("Please copy config.yaml.template to config.yaml and add your Groq API key")
        return False
    
    with open(config_path, 'r') as f:
        content = f.read()
        if "YOUR_GROQ_API_KEY_HERE" in content:
            print("Please update config.yaml with your actual Groq API key")
            return False
    
    print("Configuration looks good")
    return True

def main():
    print("Starting Secure Multi-Tenant RAG Web Interface")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("Cannot start web interface due to missing dependencies")
        return 1
    
    # Check configuration
    if not check_config():
        print("Cannot start web interface due to configuration issues")
        return 1
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs(".state/memory", exist_ok=True)
    
    print("Starting web server...")
    print("The web interface will open automatically in your browser")
    print("URL: http://localhost:5001")
    print("=" * 50)
    
    # Start the web application
    try:
        from app.web_app import app, socketio
        print("Web interface is ready!")
        print("Features:")
        print("   - Beautiful modern UI with dark/light theme")
        print("   - Real-time chat with streaming responses")
        print("   - Multi-tenant switching (U1-U4 + Public)")
        print("   - Memory management (Buffer/Summary)")
        print("   - Security indicators and citation display")
        print("   - Responsive design for all devices")
        print("=" * 50)
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(2)
            webbrowser.open("http://localhost:5001")
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start the server
        socketio.run(app, debug=False, host='0.0.0.0', port=5001)
        
    except KeyboardInterrupt:
        print("\nWeb interface stopped by user")
        return 0
    except Exception as e:
        print(f"Error starting web interface: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
