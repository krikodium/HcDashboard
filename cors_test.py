#!/usr/bin/env python3
"""
CORS Configuration Test Suite for Hermanas Caradonti Admin Tool
Focus: Testing CORS headers and cross-origin requests

This test suite validates:
- CORS headers are properly set in responses
- OPTIONS preflight requests work correctly
- Authentication works from different origins
- All API endpoints are accessible with proper CORS headers
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, List
import os
import sys

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://1df6413f-d3b2-45f2-ace0-9cd4a825711a.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class CORSAPITester:
    def __init__(self):
        self.auth_token = None
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str, data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if data and not success:
            print(f"   Data: {json.dumps(data, indent=2, default=str)}")
    
    def test_preflight_options_request(self) -> bool:
        """Test OPTIONS preflight request for CORS"""
        try:
            # Test OPTIONS request to login endpoint
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type, Authorization'
            }
            
            response = self.session.options(f"{API_BASE}/auth/login", headers=headers)
            
            if response.status_code in [200, 204]:
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                    'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
                }
                
                # Check if required CORS headers are present
                required_checks = [
                    ('Access-Control-Allow-Origin', cors_headers['Access-Control-Allow-Origin']),
                    ('Access-Control-Allow-Methods', cors_headers['Access-Control-Allow-Methods']),
                    ('Access-Control-Allow-Headers', cors_headers['Access-Control-Allow-Headers'])
                ]
                
                missing_headers = [header for header, value in required_checks if not value]
                
                if not missing_headers:
                    self.log_test("OPTIONS Preflight Request", True, 
                                f"CORS headers properly set", cors_headers)
                    return True
                else:
                    self.log_test("OPTIONS Preflight Request", False, 
                                f"Missing CORS headers: {missing_headers}", cors_headers)
                    return False
            else:
                self.log_test("OPTIONS Preflight Request", False, 
                            f"OPTIONS request failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("OPTIONS Preflight Request", False, f"Error: {str(e)}")
            return False
    
    def test_cors_headers_in_responses(self) -> bool:
        """Test that CORS headers are present in actual API responses"""
        try:
            # Test different origins
            origins_to_test = [
                'http://localhost:3000',
                'https://localhost:3000',
                'https://1df6413f-d3b2-45f2-ace0-9cd4a825711a.preview.emergentagent.com'
            ]
            
            all_passed = True
            
            for origin in origins_to_test:
                headers = {'Origin': origin}
                
                # Test health endpoint with origin header
                response = self.session.get(f"{API_BASE}/health", headers=headers)
                
                if response.status_code == 200:
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    
                    if cors_origin and (cors_origin == origin or cors_origin == '*'):
                        self.log_test(f"CORS Headers - Origin {origin}", True, 
                                    f"Access-Control-Allow-Origin: {cors_origin}")
                    else:
                        self.log_test(f"CORS Headers - Origin {origin}", False, 
                                    f"Missing or incorrect Access-Control-Allow-Origin header: {cors_origin}")
                        all_passed = False
                else:
                    self.log_test(f"CORS Headers - Origin {origin}", False, 
                                f"Health check failed: {response.status_code}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_test("CORS Headers in Responses", False, f"Error: {str(e)}")
            return False
    
    def test_authentication_with_cors(self) -> bool:
        """Test authentication endpoint with CORS headers"""
        try:
            # Test login with different origins
            origins_to_test = [
                'http://localhost:3000',
                'https://localhost:3000'
            ]
            
            login_data = {
                "username": "mateo",
                "password": "prueba123"
            }
            
            all_passed = True
            
            for origin in origins_to_test:
                headers = {'Origin': origin, 'Content-Type': 'application/json'}
                
                response = self.session.post(f"{API_BASE}/auth/login", 
                                           json=login_data, headers=headers)
                
                if response.status_code == 200:
                    auth_response = response.json()
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    
                    if cors_origin and (cors_origin == origin or cors_origin == '*'):
                        self.auth_token = auth_response["access_token"]
                        self.log_test(f"Authentication with CORS - Origin {origin}", True, 
                                    f"Login successful with CORS header: {cors_origin}")
                    else:
                        self.log_test(f"Authentication with CORS - Origin {origin}", False, 
                                    f"Login successful but missing CORS header: {cors_origin}")
                        all_passed = False
                else:
                    self.log_test(f"Authentication with CORS - Origin {origin}", False, 
                                f"Login failed: {response.status_code} - {response.text}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_test("Authentication with CORS", False, f"Error: {str(e)}")
            return False
    
    def test_authenticated_endpoints_with_cors(self) -> bool:
        """Test authenticated endpoints maintain CORS headers"""
        if not self.auth_token:
            self.log_test("Authenticated Endpoints CORS", False, "No auth token available")
            return False
        
        try:
            # Test authenticated endpoints with CORS
            endpoints_to_test = [
                '/auth/me',
                '/deco-movements',
                '/projects'
            ]
            
            headers = {
                'Origin': 'http://localhost:3000',
                'Authorization': f'Bearer {self.auth_token}'
            }
            
            all_passed = True
            
            for endpoint in endpoints_to_test:
                response = self.session.get(f"{API_BASE}{endpoint}", headers=headers)
                
                if response.status_code == 200:
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    
                    if cors_origin:
                        self.log_test(f"Authenticated CORS - {endpoint}", True, 
                                    f"CORS header present: {cors_origin}")
                    else:
                        self.log_test(f"Authenticated CORS - {endpoint}", False, 
                                    "Missing Access-Control-Allow-Origin header")
                        all_passed = False
                else:
                    self.log_test(f"Authenticated CORS - {endpoint}", False, 
                                f"Request failed: {response.status_code}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_test("Authenticated Endpoints CORS", False, f"Error: {str(e)}")
            return False
    
    def test_post_requests_with_cors(self) -> bool:
        """Test POST requests with CORS headers"""
        if not self.auth_token:
            self.log_test("POST Requests CORS", False, "No auth token available")
            return False
        
        try:
            headers = {
                'Origin': 'http://localhost:3000',
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/json'
            }
            
            # Test creating a deco movement
            movement_data = {
                "date": "2024-01-30",
                "project_name": "Pájaro",
                "description": "CORS test movement",
                "income_usd": 100.0,
                "supplier": "CORS Test Supplier",
                "reference_number": "CORS-001"
            }
            
            response = self.session.post(f"{API_BASE}/deco-movements", 
                                       json=movement_data, headers=headers)
            
            if response.status_code == 200:
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                
                if cors_origin:
                    self.log_test("POST Request CORS", True, 
                                f"POST request successful with CORS: {cors_origin}")
                    return True
                else:
                    self.log_test("POST Request CORS", False, 
                                "POST successful but missing CORS header")
                    return False
            else:
                self.log_test("POST Request CORS", False, 
                            f"POST request failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("POST Request CORS", False, f"Error: {str(e)}")
            return False
    
    def test_error_responses_with_cors(self) -> bool:
        """Test that error responses also include CORS headers"""
        try:
            headers = {'Origin': 'http://localhost:3000'}
            
            # Test with invalid credentials to trigger 401 error
            invalid_login = {
                "username": "invalid",
                "password": "invalid"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", 
                                       json=invalid_login, headers=headers)
            
            if response.status_code == 401:
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                
                if cors_origin:
                    self.log_test("Error Response CORS", True, 
                                f"Error response includes CORS header: {cors_origin}")
                    return True
                else:
                    self.log_test("Error Response CORS", False, 
                                "Error response missing CORS header")
                    return False
            else:
                self.log_test("Error Response CORS", False, 
                            f"Expected 401 error but got: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Error Response CORS", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run complete CORS test suite"""
        print("=" * 80)
        print("🌐 CORS CONFIGURATION TEST SUITE")
        print("=" * 80)
        print(f"Testing against: {API_BASE}")
        print()
        
        # Step 1: Test OPTIONS preflight requests
        print("🔍 Testing OPTIONS Preflight Requests...")
        self.test_preflight_options_request()
        
        # Step 2: Test CORS headers in responses
        print("\n📡 Testing CORS Headers in Responses...")
        self.test_cors_headers_in_responses()
        
        # Step 3: Test authentication with CORS
        print("\n🔐 Testing Authentication with CORS...")
        self.test_authentication_with_cors()
        
        # Step 4: Test authenticated endpoints with CORS
        print("\n🛡️ Testing Authenticated Endpoints with CORS...")
        self.test_authenticated_endpoints_with_cors()
        
        # Step 5: Test POST requests with CORS
        print("\n📝 Testing POST Requests with CORS...")
        self.test_post_requests_with_cors()
        
        # Step 6: Test error responses with CORS
        print("\n⚠️ Testing Error Responses with CORS...")
        self.test_error_responses_with_cors()
        
        # Summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print("📊 CORS TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🚨 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)
        
        # Save detailed results to file
        with open('/app/cors_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"📄 Detailed results saved to: /app/cors_test_results.json")

def main():
    """Main test execution"""
    tester = CORSAPITester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())