import requests
import os
import time
from datetime import datetime

def test_application(base_url):
    print(f"\n{'='*50}")
    print(f"Testing application at: {base_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    tests = {
        "Main Page": f"{base_url}",
        "Static CSS": f"{base_url}/static/css/style.css",
        "Static JS": f"{base_url}/static/js/main.js",
        "Favicon": f"{base_url}/static/favicon.ico"
    }
    
    all_passed = True
    
    for test_name, url in tests.items():
        try:
            print(f"\nTesting {test_name}...")
            response = requests.get(url, timeout=10)
            status = '✅' if response.status_code == 200 else '❌'
            print(f"Status: {status}")
            print(f"Response Code: {response.status_code}")
            print(f"Response Time: {response.elapsed.total_seconds():.2f} seconds")
            
            if response.status_code != 200:
                all_passed = False
                print(f"Error: {response.text[:200]}...")  # Print first 200 chars of error
                
        except requests.exceptions.RequestException as e:
            all_passed = False
            print(f"❌ Error: {str(e)}")
    
    print(f"\n{'='*50}")
    print(f"Overall Status: {'✅ All tests passed' if all_passed else '❌ Some tests failed'}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    # Test local deployment
    print("\nTesting local deployment:")
    test_application("http://localhost:5000")
    
    # Test Render deployment
    print("\nTesting Render deployment:")
    render_url = "https://scanlytic.onrender.com"
    test_application(render_url)
    
    # Wait a bit and test again to check for cold start
    print("\nWaiting 30 seconds to test cold start...")
    time.sleep(30)
    print("\nTesting Render deployment (cold start):")
    test_application(render_url) 