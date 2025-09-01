#!/usr/bin/env python3
"""
Simple Node.js test to isolate issues
"""
import asyncio
import json
import subprocess
import time
import httpx


async def test_step_by_step():
    """Test each component step by step"""
    
    print("🧪 STEP-BY-STEP NODE.JS TEST")
    print("="*50)
    
    # Load cookies
    with open('fresh_cookies.json', 'r') as f:
        cookies = json.load(f)
    
    print(f"✅ Loaded {len(cookies)} cookies")
    
    # Test 1: Simple health check
    print("\n1️⃣ Testing server health...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:3002/health", timeout=5.0)
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Server healthy: {health}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot reach server: {e}")
            return False
    
    # Test 2: Initialize with minimal cookies
    print("\n2️⃣ Testing initialization with minimal cookies...")
    minimal_cookies = {
        "SAPISID": cookies.get("SAPISID", ""),
        "SID": cookies.get("SID", ""),
        "__Secure-1PSID": cookies.get("__Secure-1PSID", "")
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:3002/initialize",
                json={"cookies": minimal_cookies},
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Init result: {result}")
                return result.get("success", False)
            else:
                print(f"❌ Init failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Init error: {e}")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_step_by_step())
    print(f"\nTest result: {'SUCCESS' if success else 'FAILED'}")