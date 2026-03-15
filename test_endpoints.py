#!/usr/bin/env python3
"""
Test all backend endpoints
Run this to verify everything is working
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_result(name, status, data=None):
    icon = "✅" if status == 200 else "❌"
    print(f"{icon} {name}: {status}")
    if data and status == 200:
        if isinstance(data, dict):
            print(f"   Response: {str(data)[:100]}...")
        else:
            print(f"   Response: {str(data)[:100]}...")

def test_endpoints():
    print("\n" + "="*60)
    print("🔍 TESTING BACKEND ENDPOINTS")
    print("="*60 + "\n")

    # Test 1: Root endpoint
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        print_result("GET /", r.status_code, r.json() if r.status_code == 200 else None)
    except Exception as e:
        print(f"❌ GET /: Failed - {str(e)}")

    # Test 2: Health check
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print_result("GET /api/health", r.status_code, r.json() if r.status_code == 200 else None)
    except Exception as e:
        print(f"❌ GET /api/health: Failed - {str(e)}")

    # Test 3: Metrics
    try:
        r = requests.get(f"{BASE_URL}/api/metrics", timeout=5)
        print_result("GET /api/metrics", r.status_code, r.json() if r.status_code == 200 else None)
    except Exception as e:
        print(f"❌ GET /api/metrics: Failed - {str(e)}")

    # Test 4: Dashboard
    try:
        r = requests.get(f"{BASE_URL}/api/dashboard", timeout=5)
        print_result("GET /api/dashboard", r.status_code, r.json() if r.status_code == 200 else None)
    except Exception as e:
        print(f"❌ GET /api/dashboard: Failed - {str(e)}")

    # Test 5: Chat POST
    print("\n📨 Testing POST /api/chat")
    try:
        r = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Hello, how are you?",
                "userId": "test_user",
                "sessionId": "test_session"
            },
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            print(f"✅ POST /api/chat: 200")
            print(f"   Response: {data.get('response', '')[:100]}...")
            print(f"   Intent: {data.get('intent')}")
            print(f"   Time: {data.get('processing_time_ms')}ms")
        else:
            print(f"❌ POST /api/chat: {r.status_code}")
    except Exception as e:
        print(f"❌ POST /api/chat: Failed - {str(e)}")

    # Test 6: Chat history
    try:
        r = requests.get(f"{BASE_URL}/api/chat/history/test_session", timeout=5)
        print_result("GET /api/chat/history/test_session", r.status_code)
    except Exception as e:
        print(f"❌ GET /api/chat/history: Failed - {str(e)}")

    # Test 7: Emergency SOS
    print("\n🚨 Testing POST /api/emergency/sos")
    try:
        r = requests.post(
            f"{BASE_URL}/api/emergency/sos",
            json={
                "userId": "test_user",
                "message": "Test emergency",
                "emergencyType": "medical"
            },
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            print(f"✅ POST /api/emergency/sos: 200")
            print(f"   Emergency ID: {data.get('emergency_id')}")
            print(f"   Severity: {data.get('severity')}")
            print(f"   Stage: {data.get('stage')}")
        else:
            print(f"❌ POST /api/emergency/sos: {r.status_code}")
    except Exception as e:
        print(f"❌ POST /api/emergency/sos: Failed - {str(e)}")

    # Test 8: Emergency status
    try:
        r = requests.get(f"{BASE_URL}/api/emergency/status", timeout=5)
        print_result("GET /api/emergency/status", r.status_code)
    except Exception as e:
        print(f"❌ GET /api/emergency/status: Failed - {str(e)}")

    # Test 9: Emergency contacts
    try:
        r = requests.get(f"{BASE_URL}/api/emergency/contacts", timeout=5)
        print_result("GET /api/emergency/contacts", r.status_code)
    except Exception as e:
        print(f"❌ GET /api/emergency/contacts: Failed - {str(e)}")

    # Test 10: DevOps heal
    print("\n🛠️ Testing POST /api/devops/heal")
    try:
        r = requests.post(
            f"{BASE_URL}/api/devops/heal",
            headers={"X-DevOps-Key": "devops-secret-key"},
            timeout=10
        )
        print_result("POST /api/devops/heal", r.status_code, r.json() if r.status_code == 200 else None)
    except Exception as e:
        print(f"❌ POST /api/devops/heal: Failed - {str(e)}")

    # Test 11: Hero showcase
    try:
        r = requests.get(f"{BASE_URL}/api/hero/showcase", timeout=5)
        print_result("GET /api/hero/showcase", r.status_code)
    except Exception as e:
        print(f"❌ GET /api/hero/showcase: Failed - {str(e)}")

    print("\n" + "="*60)
    print("✅ TESTING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_endpoints()