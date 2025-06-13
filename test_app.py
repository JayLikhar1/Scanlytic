import requests
import time
from datetime import datetime
import sys
import os

def test_endpoint(url, endpoint, timeout=30):
    """Test a specific endpoint with better error handling and timeout"""
    full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        start_time = time.time()
        response = requests.get(full_url, timeout=timeout)
        response_time = time.time() - start_time
        
        print(f"\nTesting {endpoint}...")
        print(f"Status: {'✅' if response.status_code == 200 else '❌'}")
        print(f"Response Code: {response.status_code}")
        print(f"Response Time: {response_time:.2f} seconds")
        
        if response.status_code != 200:
            print(f"Error: {response.text[:200]}...")
        
        return response.status_code == 200
    except requests.exceptions.Timeout:
        print(f"\nTesting {endpoint}...")
        print("❌ Error: Request timed out")
        print(f"Timeout: {timeout} seconds")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\nTesting {endpoint}...")
        print(f"❌ Error: {str(e)}")
        return False
    except Exception as e:
        print(f"\nTesting {endpoint}...")
        print(f"❌ Error: {str(e)}")
        return False

def test_deployment(url, name):
    """Test a deployment with better error handling"""
    print(f"\n{'='*50}")
    print(f"Testing {name} deployment:")
    print(f"Testing application at: {url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    success = True
    
    # Test main page
    if not test_endpoint(url, "/"):
        success = False
    
    # Test static files
    if not test_endpoint(url, "/static/css/style.css"):
        success = False
    
    if not test_endpoint(url, "/static/js/main.js"):
        success = False
    
    if not test_endpoint(url, "/static/favicon.ico"):
        success = False
    
    print(f"\n{'='*50}")
    print(f"Overall Status: {'✅ All tests passed' if success else '❌ Some tests failed'}")
    print(f"{'='*50}\n")
    
    return success

def main():
    # Test local deployment
    local_url = "http://localhost:5000"
    local_success = test_deployment(local_url, "local")
    
    # Test Render deployment
    render_url = "https://scanlytic.onrender.com"
    render_success = test_deployment(render_url, "Render")
    
    # Wait and test cold start
    print("\nWaiting 30 seconds to test cold start...")
    time.sleep(30)
    cold_start_success = test_deployment(render_url, "Render (cold start)")
    
    # Print summary
    print("\nDeployment Test Summary:")
    print(f"Local Deployment: {'✅' if local_success else '❌'}")
    print(f"Render Deployment: {'✅' if render_success else '❌'}")
    print(f"Cold Start Test: {'✅' if cold_start_success else '❌'}")

if __name__ == "__main__":
    main() 