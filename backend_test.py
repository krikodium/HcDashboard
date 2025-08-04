#!/usr/bin/env python3
"""
Backend API Test Suite for Hermanas Caradonti Admin Tool
Focus: Deco Movements Module Testing

This test suite validates the Deco Movements module backend API endpoints:
- Authentication (login)
- Creating deco movements
- Creating disbursement orders
- Retrieving movements and orders
- Data validation and error handling
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

class DecoMovementsAPITester:
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
    
    def create_sample_deco_movements(self) -> List[Dict[str, Any]]:
        """Create sample deco movements with realistic data"""
        movements_data = [
            {
                "date": "2024-01-15",
                "project_name": "Pájaro",
                "description": "Initial project funding from client",
                "income_usd": 5000.0,
                "supplier": "Cliente Pájaro SA",
                "reference_number": "PAJ-001",
                "notes": "First installment payment received"
            },
            {
                "date": "2024-01-18",
                "project_name": "Pájaro", 
                "description": "Materials purchase - marble tiles",
                "expense_usd": 1200.0,
                "supplier": "Mármoles del Sur",
                "reference_number": "MDS-2024-001",
                "notes": "Premium marble for main lobby"
            },
            {
                "date": "2024-01-20",
                "project_name": "Alvear",
                "description": "Design consultation payment",
                "income_ars": 150000.0,
                "supplier": "Estudio Alvear",
                "reference_number": "ALV-DES-001"
            },
            {
                "date": "2024-01-22",
                "project_name": "Hotel Madero",
                "description": "Furniture procurement",
                "expense_ars": 85000.0,
                "expense_usd": 300.0,
                "supplier": "Muebles Madero SRL",
                "reference_number": "MM-FUR-001",
                "notes": "Custom furniture for hotel rooms"
            },
            {
                "date": "2024-01-25",
                "project_name": "Alvear",
                "description": "Lighting fixtures expense",
                "expense_usd": 800.0,
                "supplier": "Iluminación Premium",
                "reference_number": "IP-2024-003"
            },
            {
                "date": "2024-01-28",
                "project_name": "Hotel Madero",
                "description": "Client advance payment",
                "income_usd": 3500.0,
                "income_ars": 200000.0,
                "supplier": "Hotel Madero Management",
                "reference_number": "HM-ADV-001",
                "notes": "Advance for February work"
            }
        ]
        
        created_movements = []
        
        for i, movement_data in enumerate(movements_data):
            try:
                response = self.session.post(f"{API_BASE}/deco-movements", json=movement_data)
                
                if response.status_code == 200:
                    movement = response.json()
                    created_movements.append(movement)
                    self.log_test(f"Create Movement {i+1}", True, 
                                f"Created movement for {movement_data['project_name']}: {movement_data['description'][:50]}...")
                else:
                    self.log_test(f"Create Movement {i+1}", False, 
                                f"Failed to create movement: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test(f"Create Movement {i+1}", False, f"Error creating movement: {str(e)}")
        
        return created_movements
    
    def create_sample_disbursement_orders(self) -> List[Dict[str, Any]]:
        """Create sample disbursement orders"""
        orders_data = [
            {
                "project_name": "Pájaro",
                "disbursement_type": "Supplier Payment",
                "amount_usd": 2500.0,
                "supplier": "Constructora Pájaro",
                "description": "Payment for construction materials and labor",
                "due_date": "2024-02-15",
                "priority": "High",
                "supporting_documents": ["invoice_001.pdf", "contract_pajaro.pdf"]
            },
            {
                "project_name": "Alvear",
                "disbursement_type": "Materials",
                "amount_ars": 120000.0,
                "supplier": "Materiales Alvear SRL",
                "description": "Premium wood flooring materials",
                "due_date": "2024-02-10",
                "priority": "Normal",
                "supporting_documents": ["quote_wood.pdf"]
            },
            {
                "project_name": "Hotel Madero",
                "disbursement_type": "Labor",
                "amount_usd": 1800.0,
                "amount_ars": 50000.0,
                "supplier": "Equipo Instalación Madero",
                "description": "Installation team payment for furniture setup",
                "due_date": "2024-02-05",
                "priority": "Urgent",
                "supporting_documents": ["labor_contract.pdf", "timesheet_jan.pdf"]
            }
        ]
        
        created_orders = []
        
        for i, order_data in enumerate(orders_data):
            try:
                response = self.session.post(f"{API_BASE}/deco-movements/disbursement-order", json=order_data)
                
                if response.status_code == 200:
                    order = response.json()
                    created_orders.append(order)
                    self.log_test(f"Create Disbursement Order {i+1}", True,
                                f"Created order for {order_data['project_name']}: {order_data['description'][:50]}...")
                else:
                    self.log_test(f"Create Disbursement Order {i+1}", False,
                                f"Failed to create order: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test(f"Create Disbursement Order {i+1}", False, f"Error creating order: {str(e)}")
        
        return created_orders
    
    def test_get_deco_movements(self) -> bool:
        """Test retrieving deco movements"""
        try:
            # Test basic retrieval
            response = self.session.get(f"{API_BASE}/deco-movements")
            
            if response.status_code == 200:
                movements = response.json()
                self.log_test("Get Deco Movements", True, 
                            f"Retrieved {len(movements)} movements")
                
                # Test with project filter
                response_filtered = self.session.get(f"{API_BASE}/deco-movements?project=Pájaro")
                if response_filtered.status_code == 200:
                    filtered_movements = response_filtered.json()
                    pajaro_count = len([m for m in filtered_movements if m.get('project_name') == 'Pájaro'])
                    self.log_test("Get Movements - Project Filter", True,
                                f"Retrieved {pajaro_count} movements for Pájaro project")
                else:
                    self.log_test("Get Movements - Project Filter", False,
                                f"Failed to filter by project: {response_filtered.status_code}")
                
                # Test pagination
                response_paginated = self.session.get(f"{API_BASE}/deco-movements?skip=0&limit=3")
                if response_paginated.status_code == 200:
                    paginated_movements = response_paginated.json()
                    self.log_test("Get Movements - Pagination", True,
                                f"Retrieved {len(paginated_movements)} movements with pagination")
                else:
                    self.log_test("Get Movements - Pagination", False,
                                f"Failed pagination test: {response_paginated.status_code}")
                
                return True
            else:
                self.log_test("Get Deco Movements", False,
                            f"Failed to retrieve movements: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Deco Movements", False, f"Error retrieving movements: {str(e)}")
            return False
    
    def test_get_disbursement_orders(self) -> bool:
        """Test retrieving disbursement orders"""
        try:
            # Test basic retrieval
            response = self.session.get(f"{API_BASE}/deco-movements/disbursement-order")
            
            if response.status_code == 200:
                orders = response.json()
                self.log_test("Get Disbursement Orders", True,
                            f"Retrieved {len(orders)} disbursement orders")
                
                # Test with project filter
                response_filtered = self.session.get(f"{API_BASE}/deco-movements/disbursement-order?project=Alvear")
                if response_filtered.status_code == 200:
                    filtered_orders = response_filtered.json()
                    alvear_count = len([o for o in filtered_orders if o.get('project_name') == 'Alvear'])
                    self.log_test("Get Orders - Project Filter", True,
                                f"Retrieved {alvear_count} orders for Alvear project")
                else:
                    self.log_test("Get Orders - Project Filter", False,
                                f"Failed to filter orders by project: {response_filtered.status_code}")
                
                # Test with status filter
                response_status = self.session.get(f"{API_BASE}/deco-movements/disbursement-order?status=Requested")
                if response_status.status_code == 200:
                    status_orders = response_status.json()
                    requested_count = len([o for o in status_orders if o.get('status') == 'Requested'])
                    self.log_test("Get Orders - Status Filter", True,
                                f"Retrieved {requested_count} orders with 'Requested' status")
                else:
                    self.log_test("Get Orders - Status Filter", False,
                                f"Failed to filter orders by status: {response_status.status_code}")
                
                return True
            else:
                self.log_test("Get Disbursement Orders", False,
                            f"Failed to retrieve orders: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Disbursement Orders", False, f"Error retrieving orders: {str(e)}")
            return False
    
    def test_data_validation(self) -> bool:
        """Test data validation and error handling"""
        validation_tests = [
            {
                "name": "Invalid Movement - Missing Required Fields",
                "endpoint": "/deco-movements",
                "data": {"description": "Test without required fields"},
                "expect_error": True
            },
            {
                "name": "Invalid Movement - Negative Amount",
                "endpoint": "/deco-movements", 
                "data": {
                    "date": "2024-01-30",
                    "project_name": "Pájaro",
                    "description": "Test negative amount",
                    "income_usd": -100.0
                },
                "expect_error": True
            },
            {
                "name": "Invalid Disbursement - Missing Supplier",
                "endpoint": "/deco-movements/disbursement-order",
                "data": {
                    "project_name": "Alvear",
                    "disbursement_type": "Materials",
                    "amount_usd": 1000.0,
                    "description": "Test without supplier"
                },
                "expect_error": True
            },
            {
                "name": "Invalid Disbursement - Invalid Priority",
                "endpoint": "/deco-movements/disbursement-order",
                "data": {
                    "project_name": "Alvear",
                    "disbursement_type": "Materials",
                    "amount_usd": 1000.0,
                    "supplier": "Test Supplier",
                    "description": "Test invalid priority",
                    "priority": "SuperUrgent"  # Invalid priority
                },
                "expect_error": True
            }
        ]
        
        all_passed = True
        
        for test in validation_tests:
            try:
                response = self.session.post(f"{API_BASE}{test['endpoint']}", json=test['data'])
                
                if test['expect_error']:
                    if response.status_code >= 400:
                        self.log_test(test['name'], True, f"Correctly rejected invalid data: {response.status_code}")
                    else:
                        self.log_test(test['name'], False, f"Should have rejected invalid data but got: {response.status_code}")
                        all_passed = False
                else:
                    if response.status_code == 200:
                        self.log_test(test['name'], True, "Valid data accepted")
                    else:
                        self.log_test(test['name'], False, f"Valid data rejected: {response.status_code}")
                        all_passed = False
                        
            except Exception as e:
                self.log_test(test['name'], False, f"Validation test error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_balance_calculations(self, movements: List[Dict[str, Any]]) -> bool:
        """Test that balance calculations are working correctly"""
        try:
            # Group movements by project and calculate expected balances
            project_balances = {}
            
            for movement in movements:
                project = movement.get('project_name')
                if project not in project_balances:
                    project_balances[project] = {'income_usd': 0, 'expense_usd': 0, 'income_ars': 0, 'expense_ars': 0}
                
                project_balances[project]['income_usd'] += movement.get('income_usd', 0) or 0
                project_balances[project]['expense_usd'] += movement.get('expense_usd', 0) or 0
                project_balances[project]['income_ars'] += movement.get('income_ars', 0) or 0
                project_balances[project]['expense_ars'] += movement.get('expense_ars', 0) or 0
            
            # Calculate net balances
            for project in project_balances:
                net_usd = project_balances[project]['income_usd'] - project_balances[project]['expense_usd']
                net_ars = project_balances[project]['income_ars'] - project_balances[project]['expense_ars']
                project_balances[project]['net_usd'] = net_usd
                project_balances[project]['net_ars'] = net_ars
            
            self.log_test("Balance Calculations", True, 
                        f"Calculated balances for {len(project_balances)} projects", 
                        project_balances)
            return True
            
        except Exception as e:
            self.log_test("Balance Calculations", False, f"Error calculating balances: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 80)
        print("🧪 DECO MOVEMENTS MODULE API TEST SUITE")
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
        print("📝 TESTING DECO MOVEMENTS CREATION")
        print("=" * 50)
        
        # Step 3: Create sample movements
        movements = self.create_sample_deco_movements()
        
        print("\n" + "=" * 50)
        print("📋 TESTING DISBURSEMENT ORDERS CREATION")
        print("=" * 50)
        
        # Step 4: Create sample disbursement orders
        orders = self.create_sample_disbursement_orders()
        
        print("\n" + "=" * 50)
        print("📊 TESTING DATA RETRIEVAL")
        print("=" * 50)
        
        # Step 5: Test retrieval endpoints
        self.test_get_deco_movements()
        self.test_get_disbursement_orders()
        
        print("\n" + "=" * 50)
        print("🔍 TESTING DATA VALIDATION")
        print("=" * 50)
        
        # Step 6: Test validation
        self.test_data_validation()
        
        print("\n" + "=" * 50)
        print("🧮 TESTING BALANCE CALCULATIONS")
        print("=" * 50)
        
        # Step 7: Test balance calculations
        self.test_balance_calculations(movements)
        
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
        with open('/app/deco_movements_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"📄 Detailed results saved to: /app/deco_movements_test_results.json")

def main():
    """Main test execution"""
    tester = DecoMovementsAPITester()
    
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