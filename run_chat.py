#!/usr/bin/env python3
"""
Run the chat-based Streamlit interface for the IT Approval System

Usage:
    python run_chat.py

This will start the Streamlit server with the new chat interface.
"""

import subprocess
import sys
import os

def main():
    """Run the chat-based Streamlit app"""
    print("🚀 Starting IT Approval System - Chat Interface")
    print("=" * 50)
    print("📍 URL: http://localhost:8501")
    print("💬 Interface: Chat-based natural language")
    print("🔐 Backend: http://localhost:8000 (must be running)")
    print("=" * 50)
    
    # Check if streamlit is installed
    try:
        import streamlit
        print(f"✅ Streamlit version: {streamlit.__version__}")
    except ImportError:
        print("❌ Streamlit not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
        import streamlit
    
    # Run the chat interface
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_chat.py",
            "--server.port", "8501",
            "--server.address", "127.0.0.1"
        ])
    except KeyboardInterrupt:
        print("\n👋 Chat interface stopped")
    except Exception as e:
        print(f"❌ Error starting chat interface: {e}")

if __name__ == "__main__":
    main()
