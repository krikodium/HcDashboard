#!/usr/bin/env python3
"""
Backend API Testing for Hermanas Caradonti Admin Tool
Testing General Cash Module and Application Categories functionality
"""

import requests
import json
from datetime import datetime, date
from typing import Dict, Any, Optional
import sys
import os

# Configuration
BACKEND_URL = "https://231fb371-62f5-4f18-8306-0edc3eeac6de.preview.emergentagent.com/api"
TEST_USERNAME = "admin"
TEST_PASSWORD = "changeme123"

class BackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str, details: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def authenticate(self) -> bool:
        """Authenticate and get JWT token"""
        try:
            # First try to register the user (in case it doesn't exist)
            register_data = {
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD,
                "roles": ["super-admin"]
            }
            
            register_response = requests.post(
                f"{self.base_url}/auth/register",
                json=register_data,
                headers=self.headers,
                timeout=10
            )
            
            # Registration might fail if user exists, that's okay
            if register_response.status_code == 200:
                print(f"✅ User {TEST_USERNAME} registered successfully")
            elif register_response.status_code == 400:
                print(f"ℹ️  User {TEST_USERNAME} already exists")
            else:
                print(f"⚠️  Registration response: {register_response.status_code}")
            
            # Now try to login
            login_data = {
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            }
            
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers["Authorization"] = f"Bearer {self.token}"
                self.log_test("Authentication", True, "Successfully authenticated")
                return True
            else:
                self.log_test("Authentication", False, f"Login failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_health_check(self):
        """Test basic health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, "Backend is healthy", data)
            else:
                self.log_test("Health Check", False, f"Health check failed: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Health Check", False, f"Health check error: {str(e)}")
    
    def test_application_categories_list(self):
        """Test GET /api/application-categories"""
        try:
            response = requests.get(
                f"{self.base_url}/application-categories",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                categories = response.json()
                self.log_test(
                    "Application Categories List", 
                    True, 
                    f"Retrieved {len(categories)} categories",
                    {"count": len(categories), "sample": categories[:2] if categories else []}
                )
                return categories
            else:
                self.log_test("Application Categories List", False, f"Failed: {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_test("Application Categories List", False, f"Error: {str(e)}")
            return []
    
    def test_application_categories_create(self):
        """Test POST /api/application-categories"""
        try:
            test_category = {
                "name": f"Test Category {datetime.now().strftime('%H%M%S')}",
                "category_type": "Both",
                "description": "Test category for API testing"
            }
            
            response = requests.post(
                f"{self.base_url}/application-categories",
                json=test_category,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                created_category = response.json()
                self.log_test(
                    "Application Categories Create", 
                    True, 
                    f"Created category: {created_category.get('name')}",
                    created_category
                )
                return created_category
            else:
                self.log_test("Application Categories Create", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Application Categories Create", False, f"Error: {str(e)}")
            return None
    
    def test_application_categories_autocomplete(self):
        """Test GET /api/application-categories/autocomplete"""
        try:
            # Test with search query
            params = {
                "q": "Cobranza",
                "category_type": "Income",
                "limit": 5
            }
            
            response = requests.get(
                f"{self.base_url}/application-categories/autocomplete",
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                self.log_test(
                    "Application Categories Autocomplete", 
                    True, 
                    f"Found {len(results)} matching categories",
                    {"query": "Cobranza", "results": results}
                )
                return results
            else:
                self.log_test("Application Categories Autocomplete", False, f"Failed: {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_test("Application Categories Autocomplete", False, f"Error: {str(e)}")
            return []
    
    def test_application_categories_increment_usage(self, category_id: str):
        """Test PATCH /api/application-categories/{id}/increment-usage"""
        try:
            response = requests.patch(
                f"{self.base_url}/application-categories/{category_id}/increment-usage",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "Application Categories Increment Usage", 
                    True, 
                    "Usage count incremented successfully",
                    result
                )
                return True
            else:
                self.log_test("Application Categories Increment Usage", False, f"Failed: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Application Categories Increment Usage", False, f"Error: {str(e)}")
            return False
    
    def test_application_categories_summary(self):
        """Test GET /api/application-categories/summary"""
        try:
            response = requests.get(
                f"{self.base_url}/application-categories/summary",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                summary = response.json()
                self.log_test(
                    "Application Categories Summary", 
                    True, 
                    "Retrieved categories summary",
                    summary
                )
                return summary
            else:
                self.log_test("Application Categories Summary", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Application Categories Summary", False, f"Error: {str(e)}")
            return None
    
    def test_general_cash_list(self):
        """Test GET /api/general-cash"""
        try:
            response = requests.get(
                f"{self.base_url}/general-cash",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                entries = response.json()
                self.log_test(
                    "General Cash List", 
                    True, 
                    f"Retrieved {len(entries)} general cash entries",
                    {"count": len(entries), "sample": entries[:1] if entries else []}
                )
                return entries
            else:
                self.log_test("General Cash List", False, f"Failed: {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_test("General Cash List", False, f"Error: {str(e)}")
            return []
    
    def test_general_cash_create(self):
        """Test POST /api/general-cash"""
        try:
            test_entry = {
                "date": date.today().isoformat(),
                "description": f"Test entry created at {datetime.now().strftime('%H:%M:%S')}",
                "application": "Cobranza obras",  # Using existing category
                "provider": "Flores & Decoraciones SRL",
                "income_ars": 15000.0,
                "notes": "Test entry for API validation"
            }
            
            response = requests.post(
                f"{self.base_url}/general-cash",
                json=test_entry,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                created_entry = response.json()
                self.log_test(
                    "General Cash Create", 
                    True, 
                    f"Created entry: {created_entry.get('description')}",
                    created_entry
                )
                return created_entry
            else:
                self.log_test("General Cash Create", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("General Cash Create", False, f"Error: {str(e)}")
            return None
    
    def test_general_cash_approve(self, entry_id: str):
        """Test PATCH /api/general-cash/{id} for approval"""
        try:
            # Test approval by sisters
            params = {"approval_type": "sisters"}
            
            response = requests.post(
                f"{self.base_url}/general-cash/{entry_id}/approve",
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "General Cash Approve", 
                    True, 
                    "Entry approved successfully",
                    result
                )
                return True
            else:
                self.log_test("General Cash Approve", False, f"Failed: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("General Cash Approve", False, f"Error: {str(e)}")
            return False
    
    def test_general_cash_summary(self):
        """Test GET /api/general-cash/summary"""
        try:
            response = requests.get(
                f"{self.base_url}/general-cash/summary",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                summary = response.json()
                self.log_test(
                    "General Cash Summary", 
                    True, 
                    "Retrieved general cash summary",
                    summary
                )
                return summary
            else:
                self.log_test("General Cash Summary", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("General Cash Summary", False, f"Error: {str(e)}")
            return None
    
    def test_authentication_required(self):
        """Test that endpoints require authentication"""
        try:
            # Test without token
            headers_no_auth = {"Content-Type": "application/json"}
            
            response = requests.get(
                f"{self.base_url}/general-cash",
                headers=headers_no_auth,
                timeout=10
            )
            
            if response.status_code in [401, 403]:  # Both are valid for authentication required
                self.log_test(
                    "Authentication Required", 
                    True, 
                    f"Endpoints properly require authentication (HTTP {response.status_code})"
                )
                return True
            else:
                self.log_test("Authentication Required", False, f"Expected 401/403, got {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Authentication Required", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests for General Cash Module and Application Categories")
        print("=" * 80)
        
        # Test authentication first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Test health check
        self.test_health_check()
        
        # Test authentication requirement
        self.test_authentication_required()
        
        # Test Application Categories API
        print("\n📂 Testing Application Categories API...")
        categories = self.test_application_categories_list()
        created_category = self.test_application_categories_create()
        self.test_application_categories_autocomplete()
        self.test_application_categories_summary()
        
        # Test increment usage if we have a category
        if categories and len(categories) > 0:
            category_id = categories[0].get('id')
            if category_id:
                self.test_application_categories_increment_usage(category_id)
        
        # Test General Cash API
        print("\n💰 Testing General Cash API...")
        entries = self.test_general_cash_list()
        created_entry = self.test_general_cash_create()
        self.test_general_cash_summary()
        
        # Test approval if we have an entry
        if created_entry and created_entry.get('id'):
            self.test_general_cash_approve(created_entry['id'])
        
        # Print summary
        self.print_test_summary()
        
        return True
    
    def print_test_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = BackendTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()