#!/usr/bin/env python3
"""
Run the Elder AI Guardian backend server
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    reload_enabled = os.getenv("APP_ENV", "development") == "development"
    
    print("=" * 60)
    print("🚀 ELDER AI GUARDIAN - BACKEND")
    print("=" * 60)
    print(f"Host: {host}:{port}")
    print(f"Environment: {os.getenv('APP_ENV', 'development')}")
    print(f"Auto-reload: {reload_enabled}")
    print("=" * 60)
    print("📍 API: http://localhost:8000")
    print("📍 Docs: http://localhost:8000/api/docs")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload_enabled,
        log_level="info"
    )