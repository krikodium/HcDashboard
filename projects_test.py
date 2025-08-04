#!/usr/bin/env python3
"""
Backend API Test Suite for Hermanas Caradonti Admin Tool
Focus: Dynamic Project Management System Testing

This test suite validates the new dynamic project management system:
- Authentication (login)
- Initial projects verification (created during startup)
- Creating new projects
- Retrieving projects with calculated financials
- Updating projects
- Integration with deco movements
- Validation and error handling
"""

import requests
import json
from datetime import datetime, date
from typing import Dict, Any, List
import os
import sys

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://1df6413f-d3b2-45f2-ace0-9cd4a825711a.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ProjectManagementAPITester:
    def __init__(self):
        self.auth_token = None
        self.session = requests.Session()
        self.test_results = []
        self.created_project_id = None
        self.created_project_name = None
        
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
    
    def authenticate(self) -> bool:
        """Login with test credentials"""
        try:
            login_data = {
                "username": "mateo",
                "password": "prueba123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                auth_response = response.json()
                self.auth_token = auth_response["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                self.log_test("Authentication", True, f"Successfully logged in as {auth_response['user']['username']}")
                return True
            else:
                self.log_test("Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Login error: {str(e)}")
            return False
    
    def test_health_check(self) -> bool:
        """Test basic API health"""
        try:
            response = self.session.get(f"{API_BASE}/health")
            if response.status_code == 200:
                self.log_test("Health Check", True, "API is healthy")
                return True
            else:
                self.log_test("Health Check", False, f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Health check error: {str(e)}")
            return False
    
    def test_initial_projects_verification(self) -> bool:
        """Test that initial projects were created during startup"""
        try:
            response = self.session.get(f"{API_BASE}/projects")
            
            if response.status_code == 200:
                projects = response.json()
                
                # Expected initial projects
                expected_projects = ["Pájaro", "Alvear", "Hotel Madero", "Bahía Bustamante", "Palacio Duhau"]
                found_projects = [p["name"] for p in projects]
                
                missing_projects = [p for p in expected_projects if p not in found_projects]
                
                if not missing_projects:
                    self.log_test("Initial Projects Verification", True, 
                                f"All {len(expected_projects)} initial projects found: {', '.join(expected_projects)}")
                    
                    # Verify project details
                    for project in projects:
                        if project["name"] in expected_projects:
                            required_fields = ["id", "name", "description", "project_type", "status", "created_by", "created_at"]
                            missing_fields = [field for field in required_fields if field not in project or project[field] is None]
                            
                            if missing_fields:
                                self.log_test(f"Project {project['name']} Structure", False, 
                                            f"Missing required fields: {missing_fields}")
                            else:
                                self.log_test(f"Project {project['name']} Structure", True, 
                                            f"All required fields present")
                    
                    return True
                else:
                    self.log_test("Initial Projects Verification", False, 
                                f"Missing initial projects: {missing_projects}")
                    return False
            else:
                self.log_test("Initial Projects Verification", False, 
                            f"Failed to retrieve projects: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Initial Projects Verification", False, f"Error verifying initial projects: {str(e)}")
            return False
    
    def test_create_new_project(self) -> bool:
        """Test creating a new project"""
        try:
            project_data = {
                "name": f"Test Project Automation {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": "Automated test project for API validation",
                "project_type": "Deco",
                "status": "Active",
                "budget_usd": 15000.0,
                "budget_ars": 750000.0,
                "client_name": "Test Client Corp",
                "location": "Buenos Aires, Argentina"
            }
            
            response = self.session.post(f"{API_BASE}/projects", json=project_data)
            
            if response.status_code == 200:
                project = response.json()
                self.created_project_id = project["id"]
                self.created_project_name = project["name"]
                
                # Verify all fields are present
                required_fields = ["id", "name", "description", "project_type", "status", "budget_usd", "budget_ars", 
                                 "client_name", "location", "created_by", "created_at", "updated_at", "is_archived"]
                missing_fields = [field for field in required_fields if field not in project]
                
                if not missing_fields:
                    self.log_test("Create New Project", True, 
                                f"Successfully created project '{project['name']}' with ID: {project['id']}")
                    
                    # Verify default values
                    if project["is_archived"] == False and project["created_by"] == "mateo":
                        self.log_test("Project Default Values", True, "Default values set correctly")
                    else:
                        self.log_test("Project Default Values", False, 
                                    f"Default values incorrect: is_archived={project['is_archived']}, created_by={project['created_by']}")
                    
                    return True
                else:
                    self.log_test("Create New Project", False, f"Missing fields in response: {missing_fields}")
                    return False
            else:
                self.log_test("Create New Project", False, 
                            f"Failed to create project: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create New Project", False, f"Error creating project: {str(e)}")
            return False
    
    def test_get_specific_project(self) -> bool:
        """Test retrieving a specific project with calculated financials"""
        if not self.created_project_id:
            self.log_test("Get Specific Project", False, "No project ID available for testing")
            return False
        
        try:
            response = self.session.get(f"{API_BASE}/projects/{self.created_project_id}")
            
            if response.status_code == 200:
                project = response.json()
                
                # Verify financial fields are present (should be calculated)
                financial_fields = ["current_balance_usd", "current_balance_ars", "total_income_usd", 
                                  "total_expense_usd", "total_income_ars", "total_expense_ars", 
                                  "movements_count", "disbursement_orders_count"]
                
                missing_financial_fields = [field for field in financial_fields if field not in project]
                
                if not missing_financial_fields:
                    self.log_test("Get Specific Project", True, 
                                f"Retrieved project with calculated financials: {project['name']}")
                    
                    # Log financial summary
                    financial_summary = {
                        "balance_usd": project.get("current_balance_usd", 0),
                        "balance_ars": project.get("current_balance_ars", 0),
                        "movements_count": project.get("movements_count", 0),
                        "disbursement_orders_count": project.get("disbursement_orders_count", 0)
                    }
                    self.log_test("Project Financial Calculations", True, 
                                "Financial fields calculated", financial_summary)
                    
                    return True
                else:
                    self.log_test("Get Specific Project", False, 
                                f"Missing financial fields: {missing_financial_fields}")
                    return False
            else:
                self.log_test("Get Specific Project", False, 
                            f"Failed to retrieve project: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Specific Project", False, f"Error retrieving project: {str(e)}")
            return False
    
    def test_update_project(self) -> bool:
        """Test updating a project"""
        if not self.created_project_id:
            self.log_test("Update Project", False, "No project ID available for testing")
            return False
        
        try:
            update_data = {
                "description": "Updated automated test project description",
                "status": "On Hold",
                "budget_usd": 18000.0
            }
            
            response = self.session.patch(f"{API_BASE}/projects/{self.created_project_id}", json=update_data)
            
            if response.status_code == 200:
                updated_project = response.json()
                
                # Verify updates were applied
                if (updated_project["description"] == update_data["description"] and
                    updated_project["status"] == update_data["status"] and
                    updated_project["budget_usd"] == update_data["budget_usd"]):
                    
                    self.log_test("Update Project", True, 
                                f"Successfully updated project: {updated_project['name']}")
                    
                    # Verify updated_at and updated_by fields
                    if "updated_by" in updated_project and updated_project["updated_by"] == "mateo":
                        self.log_test("Project Update Metadata", True, "Update metadata set correctly")
                    else:
                        self.log_test("Project Update Metadata", False, "Update metadata not set correctly")
                    
                    return True
                else:
                    self.log_test("Update Project", False, "Updates were not applied correctly")
                    return False
            else:
                self.log_test("Update Project", False, 
                            f"Failed to update project: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Update Project", False, f"Error updating project: {str(e)}")
            return False
    
    def test_integration_with_movements(self) -> bool:
        """Test integration between projects and deco movements"""
        if not self.created_project_name:
            self.log_test("Integration with Movements", False, "No project name available for testing")
            return False
        
        try:
            # Create a deco movement with the newly created project name
            movement_data = {
                "date": "2024-01-30",
                "project_name": self.created_project_name,
                "description": "Test movement for project integration",
                "income_usd": 2500.0,
                "supplier": "Test Integration Supplier",
                "reference_number": "INT-TEST-001",
                "notes": "Testing project-movement integration"
            }
            
            response = self.session.post(f"{API_BASE}/deco-movements", json=movement_data)
            
            if response.status_code == 200:
                movement = response.json()
                
                if movement["project_name"] == self.created_project_name:
                    self.log_test("Create Movement with New Project", True, 
                                f"Successfully created movement for project: {self.created_project_name}")
                    
                    # Now retrieve the project again to see if financials are updated
                    project_response = self.session.get(f"{API_BASE}/projects/{self.created_project_id}")
                    
                    if project_response.status_code == 200:
                        updated_project = project_response.json()
                        
                        # Check if the movement is reflected in project financials
                        if (updated_project.get("movements_count", 0) > 0 and 
                            updated_project.get("total_income_usd", 0) >= 2500.0):
                            
                            self.log_test("Project-Movement Integration", True, 
                                        f"Movement correctly integrated - Income: ${updated_project.get('total_income_usd', 0)}, Count: {updated_project.get('movements_count', 0)}")
                            return True
                        else:
                            self.log_test("Project-Movement Integration", False, 
                                        f"Movement not reflected in project financials - Income: ${updated_project.get('total_income_usd', 0)}, Count: {updated_project.get('movements_count', 0)}")
                            return False
                    else:
                        self.log_test("Project-Movement Integration", False, 
                                    f"Failed to retrieve updated project: {project_response.status_code}")
                        return False
                else:
                    self.log_test("Create Movement with New Project", False, 
                                f"Movement project name mismatch: expected {self.created_project_name}, got {movement['project_name']}")
                    return False
            else:
                self.log_test("Create Movement with New Project", False, 
                            f"Failed to create movement: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Integration with Movements", False, f"Error testing integration: {str(e)}")
            return False
    
    def test_validation_and_error_handling(self) -> bool:
        """Test validation and error handling"""
        validation_tests = [
            {
                "name": "Duplicate Project Name",
                "data": {
                    "name": "Pájaro",  # This should already exist
                    "description": "Duplicate name test",
                    "project_type": "Deco",
                    "status": "Active"
                },
                "expect_error": True,
                "expected_status": 400
            },
            {
                "name": "Missing Required Fields",
                "data": {
                    "description": "Missing name field"
                },
                "expect_error": True,
                "expected_status": 422
            },
            {
                "name": "Movement with Non-existent Project",
                "endpoint": "/deco-movements",
                "data": {
                    "date": "2024-01-30",
                    "project_name": "Non-Existent Project XYZ",
                    "description": "Test with non-existent project",
                    "income_usd": 1000.0,
                    "supplier": "Test Supplier"
                },
                "expect_error": False,  # Should work as project_name is just a string now
                "expected_status": 200
            }
        ]
        
        all_passed = True
        
        for test in validation_tests:
            try:
                endpoint = test.get("endpoint", "/projects")
                response = self.session.post(f"{API_BASE}{endpoint}", json=test["data"])
                
                if test["expect_error"]:
                    if response.status_code >= 400:
                        self.log_test(test["name"], True, 
                                    f"Correctly rejected invalid data: {response.status_code}")
                    else:
                        self.log_test(test["name"], False, 
                                    f"Should have rejected invalid data but got: {response.status_code}")
                        all_passed = False
                else:
                    if response.status_code == test["expected_status"]:
                        self.log_test(test["name"], True, 
                                    f"Valid data accepted: {response.status_code}")
                    else:
                        self.log_test(test["name"], False, 
                                    f"Expected {test['expected_status']} but got: {response.status_code}")
                        all_passed = False
                        
            except Exception as e:
                self.log_test(test["name"], False, f"Validation test error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_projects_summary(self) -> bool:
        """Test projects summary endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/projects/summary")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Verify summary fields
                required_fields = ["total_projects", "active_projects", "completed_projects", 
                                 "on_hold_projects", "cancelled_projects", "total_budget_usd", 
                                 "total_budget_ars", "total_expenses_usd", "total_expenses_ars", 
                                 "projects_over_budget"]
                
                missing_fields = [field for field in required_fields if field not in summary]
                
                if not missing_fields:
                    self.log_test("Projects Summary", True, 
                                f"Summary retrieved successfully - Total projects: {summary['total_projects']}")
                    
                    # Log key metrics
                    metrics = {
                        "total_projects": summary["total_projects"],
                        "active_projects": summary["active_projects"],
                        "total_budget_usd": summary["total_budget_usd"],
                        "projects_over_budget": summary["projects_over_budget"]
                    }
                    self.log_test("Summary Metrics", True, "Key metrics calculated", metrics)
                    
                    return True
                else:
                    self.log_test("Projects Summary", False, f"Missing summary fields: {missing_fields}")
                    return False
            else:
                self.log_test("Projects Summary", False, 
                            f"Failed to retrieve summary: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Projects Summary", False, f"Error retrieving summary: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 80)
        print("🏗️  DYNAMIC PROJECT MANAGEMENT SYSTEM API TEST SUITE")
        print("=" * 80)
        print(f"Testing against: {API_BASE}")
        print()
        
        # Step 1: Health check
        if not self.test_health_check():
            print("❌ Health check failed - aborting tests")
            return False
        
        # Step 2: Authentication
        if not self.authenticate():
            print("❌ Authentication failed - aborting tests")
            return False
        
        print("\n" + "=" * 50)
        print("🔍 TESTING INITIAL PROJECTS VERIFICATION")
        print("=" * 50)
        
        # Step 3: Verify initial projects
        self.test_initial_projects_verification()
        
        print("\n" + "=" * 50)
        print("➕ TESTING PROJECT CREATION")
        print("=" * 50)
        
        # Step 4: Create new project
        self.test_create_new_project()
        
        print("\n" + "=" * 50)
        print("📊 TESTING PROJECT RETRIEVAL & FINANCIALS")
        print("=" * 50)
        
        # Step 5: Test project retrieval with financials
        self.test_get_specific_project()
        
        print("\n" + "=" * 50)
        print("✏️  TESTING PROJECT UPDATES")
        print("=" * 50)
        
        # Step 6: Test project updates
        self.test_update_project()
        
        print("\n" + "=" * 50)
        print("🔗 TESTING PROJECT-MOVEMENT INTEGRATION")
        print("=" * 50)
        
        # Step 7: Test integration with movements
        self.test_integration_with_movements()
        
        print("\n" + "=" * 50)
        print("🔍 TESTING VALIDATION & ERROR HANDLING")
        print("=" * 50)
        
        # Step 8: Test validation
        self.test_validation_and_error_handling()
        
        print("\n" + "=" * 50)
        print("📈 TESTING PROJECTS SUMMARY")
        print("=" * 50)
        
        # Step 9: Test summary endpoint
        self.test_projects_summary()
        
        # Summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
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
        with open('/app/projects_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"📄 Detailed results saved to: /app/projects_test_results.json")

def main():
    """Main test execution"""
    tester = ProjectManagementAPITester()
    
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