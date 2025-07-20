#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tests/test_local_api_debug.py
import requests
import json
import os
import sys

# Add parent directory to path to import from kognys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_local_api():
    """Test the API locally to debug any issues."""
    
    # Test the production API with the same request that's failing
    url = "https://kognys-agents-python-production.up.railway.app/papers"
    
    payload = {
        "message": "give me a research about tests in animals",
        "user_id": "0x6604ef12fb993b31aeaae18e925b6726e0a3678b"
    }
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing API endpoint...")
    print(f"📍 URL: {url}")
    print(f"📝 Payload: {json.dumps(payload, indent=2)}")
    print("="*50)
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print("📄 Response Body:")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
        except json.JSONDecodeError:
            print(response.text)
            
        if response.status_code != 200:
            print("❌ Request failed!")
            return False
        else:
            print("✅ Request succeeded!")
            return True
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 30 seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed with exception: {e}")
        return False

def test_health_check():
    """Test the health check endpoint first."""
    url = "https://kognys-agents-python-production.up.railway.app/"
    
    print("🏥 Testing health check...")
    try:
        response = requests.get(url, timeout=10)
        print(f"📊 Health check status: {response.status_code}")
        if response.status_code == 200:
            print("✅ API is alive!")
            return True
        else:
            print("❌ API health check failed!")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting API Debug Test...")
    print("="*50)
    
    # First test health
    if not test_health_check():
        print("❌ Exiting: API health check failed")
        sys.exit(1)
    
    print("\n" + "="*50)
    
    # Then test the problematic endpoint
    success = test_local_api()
    
    print("\n" + "="*50)
    if success:
        print("🎉 All tests passed!")
    else:
        print("❌ Tests failed - check the error details above")
        sys.exit(1) 