"""
Test script for rate limiting.
Makes multiple requests to /credits/summarize endpoint to test rate limiting.
"""

import requests
import time
import sys

# Configuration
BASE_URL = "http://localhost:8000"
# You'll need a valid JWT token
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjNTEzNTk2Mi02ZDQ3LTQ5NDktYjQ4Yy03OGY3NjdmNDgyMjciLCJlbWFpbCI6ImJvc3N1dGthcnNoLjMwQGdtYWlsLmNvbSIsImV4cCI6MTc3MjUyMTYyMX0.brlHO3GcF2uiLwIJ7YoxSHC7rLyEsYZ9nB0Nur0ns5w"

# Number of requests to make
NUM_REQUESTS = 25

# Headers with JWT token
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Request body
DATA = {
    "text": "This is a test text for summarizing. It needs to be at least 10 characters long to pass validation."
}


def test_rate_limiting():
    """Test rate limiting by making multiple requests."""
    
    print(f"Testing rate limiting...")
    print(f"Making {NUM_REQUESTS} requests to {BASE_URL}/credits/summarize")
    print(f"Rate limit: 20 requests per minute")
    print("-" * 50)
    
    success_count = 0
    rate_limited_count = 0
    error_count = 0
    
    for i in range(1, NUM_REQUESTS + 1):
        try:
            response = requests.post(
                f"{BASE_URL}/credits/summarize",
                headers=HEADERS,
                json=DATA,
                timeout=10
            )
            
            if response.status_code == 200:
                success_count += 1
                print(f"Request {i}: ✅ Success (200)")
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"Request {i}: ⚠️ Rate Limited (429)")
                print(f"   Response: {response.json()}")
            elif response.status_code == 401:
                print(f"Request {i}: ❌ Unauthorized (401) - Check your JWT token")
                error_count += 1
            else:
                print(f"Request {i}: ❌ Error ({response.status_code})")
                print(f"   Response: {response.text}")
                error_count += 1
                
        except requests.exceptions.ConnectionError:
            print(f"Request {i}: ❌ Connection Error - Is the server running?")
            error_count += 1
        except Exception as e:
            print(f"Request {i}: ❌ Exception: {e}")
            error_count += 1
        
        # Small delay between requests
        time.sleep(0.1)
    
    print("-" * 50)
    print(f"Results:")
    print(f"  ✅ Success: {success_count}")
    print(f"  ⚠️ Rate Limited: {rate_limited_count}")
    print(f"  ❌ Errors: {error_count}")
    print()
    
    if rate_limited_count > 0:
        print("✅ Rate limiting is working!")
    else:
        print("⚠️ No rate limiting detected (might need more requests)")


def test_input_validation():
    """Test input validation."""
    
    print("\nTesting input validation...")
    print("-" * 50)
    
    # Test 1: Empty text
    print("Test 1: Empty text")
    response = requests.post(
        f"{BASE_URL}/credits/summarize",
        headers=HEADERS,
        json={"text": ""},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 422:
        print("✅ Validation working (422)")
    else:
        print(f"Response: {response.text}")
    
    # Test 2: Text too short
    print("\nTest 2: Text too short (< 10 chars)")
    response = requests.post(
        f"{BASE_URL}/credits/summarize",
        headers=HEADERS,
        json={"text": "short"},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 422:
        print("✅ Validation working (422)")
    else:
        print(f"Response: {response.text}")
    
    # Test 3: Valid text
    print("\nTest 3: Valid text (>= 10 chars)")
    response = requests.post(
        f"{BASE_URL}/credits/summarize",
        headers=HEADERS,
        json={"text": "This is valid text for testing"},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Valid request working")
    else:
        print(f"Response: {response.text}")


if __name__ == "__main__":
    # Check if token is set
    if TOKEN == "YOUR_JWT_TOKEN_HERE":
        print("⚠️  Please set your JWT token in the script!")
        print("   Edit test_rate_limit.py and replace TOKEN with your JWT token")
        sys.exit(1)
    
    # Run tests
    test_rate_limiting()
    test_input_validation()
