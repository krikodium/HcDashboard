#!/usr/bin/env python3
"""
Backend API Testing for Hermanas Caradonti Admin Tool
Focused testing on actually implemented endpoints
"""

import requests
import json
from datetime import datetime, date
from typing import Dict, Any, Optional
import sys
import os

# Configuration - Using correct URLs and credentials
BACKEND_URL = "http://localhost:8001/api"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

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
    
    def test_health_check(self):
        """Test /api/test endpoint"""
        try:
            response = requests.get(f"{self.base_url}/test", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, "Backend is healthy", data)
                return True
            else:
                self.log_test("Health Check", False, f"Health check failed: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Health check error: {str(e)}")
            return False
    
    def authenticate(self) -> bool:
        """Authenticate and get JWT token"""
        try:
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
                user_info = data.get("user", {})
                self.log_test("Authentication", True, f"Successfully authenticated as {user_info.get('username')}", data)
                return True
            else:
                self.log_test("Authentication", False, f"Login failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_user_info(self):
        """Test /api/auth/me endpoint"""
        try:
            response = requests.get(
                f"{self.base_url}/auth/me",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.log_test("User Info", True, f"Retrieved user info for {user_data.get('username')}", user_data)
                return user_data
            else:
                self.log_test("User Info", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("User Info", False, f"Error: {str(e)}")
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
                "entry_type": "INCOME",
                "amount_ars": 15000.0,
                "approval_status": "PENDING"
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
        """Test POST /api/general-cash/{entry_id}/approve"""
        try:
            response = requests.post(
                f"{self.base_url}/general-cash/{entry_id}/approve",
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
    
    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        try:
            invalid_login_data = {
                "username": "invalid_user",
                "password": "invalid_password"
            }
            
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=invalid_login_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test(
                    "Invalid Credentials", 
                    True, 
                    "Invalid credentials properly rejected"
                )
                return True
            else:
                self.log_test("Invalid Credentials", False, f"Expected 401, got {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Invalid Credentials", False, f"Error: {str(e)}")
            return False
    
    def test_general_cash_workflow(self):
        """Test complete general cash workflow"""
        try:
            # Create an entry
            created_entry = self.test_general_cash_create()
            if not created_entry:
                return False
            
            entry_id = created_entry.get('id')
            if not entry_id:
                self.log_test("General Cash Workflow", False, "Created entry has no ID")
                return False
            
            # Approve the entry
            approval_success = self.test_general_cash_approve(entry_id)
            if not approval_success:
                return False
            
            # Get updated summary
            summary = self.test_general_cash_summary()
            if not summary:
                return False
            
            self.log_test(
                "General Cash Workflow", 
                True, 
                "Complete workflow executed successfully",
                {"entry_id": entry_id, "summary": summary}
            )
            return True
            
        except Exception as e:
            self.log_test("General Cash Workflow", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests for implemented endpoints"""
        print("🚀 Starting Backend API Tests for Hermanas Caradonti Admin Tool")
        print("=" * 80)
        
        # Test health check first (no auth required)
        health_ok = self.test_health_check()
        if not health_ok:
            print("❌ Health check failed. Backend may not be running.")
            return False
        
        # Test invalid credentials
        self.test_invalid_credentials()
        
        # Test authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Test user info
        self.test_user_info()
        
        # Test authentication requirement
        self.test_authentication_required()
        
        # Test General Cash endpoints
        self.test_general_cash_list()
        self.test_general_cash_summary()
        
        # Test complete workflow
        self.test_general_cash_workflow()
        
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