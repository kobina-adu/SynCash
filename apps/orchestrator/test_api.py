"""
Simple test script to verify the SyncCash Orchestrator API
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_orchestrator_api():
    """Test the orchestrator API endpoints"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("Testing SyncCash Orchestrator API...")
        print("=" * 50)
        
        # Test 1: Basic health check
        print("1. Testing basic health check...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("[PASS] Health check passed")
                print(f"   Response: {response.json()}")
            else:
                print(f"[FAIL] Health check failed: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Health check error: {e}")
        
        print()
        
        # Test 2: API root endpoint
        print("2. Testing root endpoint...")
        try:
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                print("[PASS] Root endpoint passed")
                print(f"   Response: {response.json()}")
            else:
                print(f"[FAIL] Root endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Root endpoint error: {e}")
        
        print()
        
        # Test 3: API documentation
        print("3. Testing API documentation...")
        try:
            response = await client.get(f"{base_url}/api/docs")
            if response.status_code == 200:
                print("[PASS] API docs accessible")
            else:
                print(f"[FAIL] API docs failed: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] API docs error: {e}")
        
        print()
        
        # Test 4: Health check endpoints
        print("4. Testing health endpoints...")
        health_endpoints = [
            "/api/v1/health",
            "/api/v1/health/detailed", 
            "/api/v1/health/ready",
            "/api/v1/health/live"
        ]
        
        for endpoint in health_endpoints:
            try:
                response = await client.get(f"{base_url}{endpoint}")
                if response.status_code in [200, 503]:  # 503 is expected if DB/Redis not available
                    print(f"[PASS] {endpoint} - Status: {response.status_code}")
                else:
                    print(f"[FAIL] {endpoint} - Status: {response.status_code}")
            except Exception as e:
                print(f"[ERROR] {endpoint} error: {e}")
        
        print()
        print("=" * 50)
        print("API testing completed!")
        print()
        print("Next steps:")
        print("- Start PostgreSQL and Redis for full functionality")
        print("- Test payment endpoints with database connectivity")
        print("- Set up Celery workers for background processing")

if __name__ == "__main__":
    asyncio.run(test_orchestrator_api())
