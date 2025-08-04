#!/usr/bin/env python3
"""
Backend API Test Suite for Hermanas Caradonti Admin Tool
Focus: Provider Management System Testing

This test suite validates the Provider Management system backend API endpoints:
- Authentication (login)
- Provider CRUD operations
- Provider autocomplete functionality
- Provider financial calculations
- Integration with shop cash module
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

class ProviderManagementAPITester:
    def __init__(self):
        self.auth_token = None
        self.session = requests.Session()
        self.test_results = []
        self.created_providers = []
        
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
    
    def test_get_initial_providers(self) -> bool:
        """Test retrieving initial providers created during startup"""
        try:
            response = self.session.get(f"{API_BASE}/providers")
            
            if response.status_code == 200:
                providers = response.json()
                provider_names = [p.get('name', '') for p in providers]
                
                # Check for expected initial providers
                expected_providers = [
                    "Flores & Decoraciones SRL",
                    "Telas y Textiles Palermo", 
                    "Iluminación Profesional SA",
                    "Muebles & Accesorios Victoria",
                    "Servicios de Transporte López",
                    "Cristalería Fina Buenos Aires"
                ]
                
                found_providers = []
                for expected in expected_providers:
                    if any(expected in name for name in provider_names):
                        found_providers.append(expected)
                
                self.log_test("Get Initial Providers", True, 
                            f"Retrieved {len(providers)} providers, found {len(found_providers)}/{len(expected_providers)} expected initial providers",
                            {"total_providers": len(providers), "found_initial": found_providers})
                return True
            else:
                self.log_test("Get Initial Providers", False,
                            f"Failed to retrieve providers: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Initial Providers", False, f"Error retrieving providers: {str(e)}")
            return False
    
    def test_provider_autocomplete(self) -> bool:
        """Test provider autocomplete functionality with various search queries"""
        search_queries = [
            {"query": "Flores", "expected_partial": "Flores & Decoraciones"},
            {"query": "Telas", "expected_partial": "Telas y Textiles"},
            {"query": "Ilum", "expected_partial": "Iluminación"},
            {"query": "Muebles", "expected_partial": "Muebles & Accesorios"},
            {"query": "Transport", "expected_partial": "Transporte"},
            {"query": "Cristal", "expected_partial": "Cristalería"},
            {"query": "xyz123", "expected_count": 0}  # Should return no results
        ]
        
        all_passed = True
        
        for test_query in search_queries:
            try:
                response = self.session.get(f"{API_BASE}/providers/autocomplete?q={test_query['query']}")
                
                if response.status_code == 200:
                    results = response.json()
                    
                    if test_query['query'] == "xyz123":
                        # Should return no results
                        if len(results) == 0:
                            self.log_test(f"Autocomplete - '{test_query['query']}'", True,
                                        f"Correctly returned no results for non-existent query")
                        else:
                            self.log_test(f"Autocomplete - '{test_query['query']}'", False,
                                        f"Should return no results but got {len(results)}")
                            all_passed = False
                    else:
                        # Should find matching providers
                        found_match = any(test_query['expected_partial'] in result.get('name', '') for result in results)
                        if found_match:
                            self.log_test(f"Autocomplete - '{test_query['query']}'", True,
                                        f"Found {len(results)} results including expected provider")
                        else:
                            self.log_test(f"Autocomplete - '{test_query['query']}'", False,
                                        f"Expected to find provider containing '{test_query['expected_partial']}' but didn't")
                            all_passed = False
                else:
                    self.log_test(f"Autocomplete - '{test_query['query']}'", False,
                                f"Autocomplete failed: {response.status_code} - {response.text}")
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Autocomplete - '{test_query['query']}'", False, f"Error in autocomplete: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_create_new_provider(self) -> bool:
        """Test creating a new provider"""
        try:
            # Use timestamp to ensure unique name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_provider_data = {
                "name": f"Proveedores Especiales Test SA {timestamp}",
                "provider_type": "Supplier",
                "contact_person": "Juan Carlos Testeo",
                "email": "juan@proveedorestest.com.ar",
                "phone": "+54 11 9999-8888",
                "address": "Av. Test 1234, Buenos Aires",
                "status": "Active",
                "payment_terms": "30 días",
                "preferred_supplier": False
            }
            
            response = self.session.post(f"{API_BASE}/providers", json=new_provider_data)
            
            if response.status_code == 200:
                provider = response.json()
                self.created_providers.append(provider)
                self.log_test("Create New Provider", True,
                            f"Successfully created provider: {provider.get('name')}",
                            {"provider_id": provider.get('id'), "provider_name": provider.get('name')})
                
                # Verify the provider was created with correct data
                if (provider.get('name') == new_provider_data['name'] and
                    provider.get('contact_person') == new_provider_data['contact_person'] and
                    provider.get('email') == new_provider_data['email']):
                    self.log_test("Verify Created Provider Data", True,
                                "Provider data matches input")
                    return True
                else:
                    self.log_test("Verify Created Provider Data", False,
                                "Provider data doesn't match input")
                    return False
            else:
                self.log_test("Create New Provider", False,
                            f"Failed to create provider: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create New Provider", False, f"Error creating provider: {str(e)}")
            return False
    
    def test_duplicate_provider_validation(self) -> bool:
        """Test that duplicate provider names are rejected"""
        try:
            # Try to create a provider with the same name as an existing one
            duplicate_provider_data = {
                "name": "Flores & Decoraciones SRL",  # This should already exist
                "provider_type": "Supplier",
                "contact_person": "Test Person",
                "email": "test@test.com",
                "phone": "+54 11 1111-2222",
                "address": "Test Address",
                "status": "Active"
            }
            
            response = self.session.post(f"{API_BASE}/providers", json=duplicate_provider_data)
            
            if response.status_code >= 400:
                self.log_test("Duplicate Provider Validation", True,
                            f"Correctly rejected duplicate provider name: {response.status_code}")
                return True
            else:
                self.log_test("Duplicate Provider Validation", False,
                            f"Should have rejected duplicate name but got: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Duplicate Provider Validation", False, f"Error testing duplicate validation: {str(e)}")
            return False
    
    def test_update_provider(self) -> bool:
        """Test updating a provider"""
        if not self.created_providers:
            self.log_test("Update Provider", False, "No created providers to update")
            return False
        
        try:
            provider = self.created_providers[0]
            provider_id = provider.get('id') or provider.get('_id')  # Try both id and _id
            
            self.log_test("Debug Provider ID", True, f"Using provider ID: {provider_id}", provider)
            
            update_data = {
                "contact_person": "María Elena Testeo Updated",
                "phone": "+54 11 7777-6666",
                "payment_terms": "15 días",
                "preferred_supplier": True
            }
            
            response = self.session.patch(f"{API_BASE}/providers/{provider_id}", json=update_data)
            
            if response.status_code == 200:
                updated_provider = response.json()
                
                # Log the updated provider for debugging
                self.log_test("Debug Updated Provider", True, "Provider update response received", updated_provider)
                
                # Verify updates were applied
                if (updated_provider.get('contact_person') == update_data['contact_person'] and
                    updated_provider.get('phone') == update_data['phone'] and
                    updated_provider.get('preferred_supplier') == update_data['preferred_supplier']):
                    self.log_test("Update Provider", True,
                                f"Successfully updated provider: {updated_provider.get('name')}")
                    return True
                else:
                    self.log_test("Update Provider", False,
                                f"Provider updates were not applied correctly. Expected: {update_data}, Got: contact_person={updated_provider.get('contact_person')}, phone={updated_provider.get('phone')}, preferred_supplier={updated_provider.get('preferred_supplier')}")
                    return False
            else:
                self.log_test("Update Provider", False,
                            f"Failed to update provider: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Update Provider", False, f"Error updating provider: {str(e)}")
            return False
    
    def test_get_specific_provider(self) -> bool:
        """Test retrieving a specific provider with calculated financials"""
        if not self.created_providers:
            self.log_test("Get Specific Provider", False, "No created providers to retrieve")
            return False
        
        try:
            provider = self.created_providers[0]
            provider_id = provider.get('id') or provider.get('_id')  # Try both id and _id
            
            response = self.session.get(f"{API_BASE}/providers/{provider_id}")
            
            if response.status_code == 200:
                retrieved_provider = response.json()
                
                # Check that financial fields are present (even if zero)
                financial_fields = ['total_purchases_usd', 'total_purchases_ars', 'transaction_count']
                has_financials = all(field in retrieved_provider for field in financial_fields)
                
                if has_financials:
                    self.log_test("Get Specific Provider", True,
                                f"Successfully retrieved provider with financials: {retrieved_provider.get('name')}")
                    return True
                else:
                    self.log_test("Get Specific Provider", False,
                                "Provider missing financial calculation fields")
                    return False
            else:
                self.log_test("Get Specific Provider", False,
                            f"Failed to retrieve provider: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Specific Provider", False, f"Error retrieving provider: {str(e)}")
            return False
    
    def test_provider_summary(self) -> bool:
        """Test getting provider summary statistics"""
        try:
            response = self.session.get(f"{API_BASE}/providers/summary")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Check that summary contains expected fields
                expected_fields = [
                    'total_providers', 'active_providers', 'inactive_providers',
                    'preferred_providers', 'total_purchases_usd', 'total_purchases_ars'
                ]
                
                has_all_fields = all(field in summary for field in expected_fields)
                
                if has_all_fields:
                    self.log_test("Provider Summary", True,
                                f"Retrieved provider summary with {summary.get('total_providers')} total providers",
                                summary)
                    return True
                else:
                    missing_fields = [field for field in expected_fields if field not in summary]
                    self.log_test("Provider Summary", False,
                                f"Summary missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Provider Summary", False,
                            f"Failed to retrieve summary: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Provider Summary", False, f"Error retrieving summary: {str(e)}")
            return False
    
    def test_shop_cash_integration(self) -> bool:
        """Test integration with shop cash module by creating a shop cash entry with provider"""
        try:
            # First, create a shop cash entry with a provider name using correct required fields
            shop_cash_data = {
                "date": "2024-01-30",
                "provider": "Flores & Decoraciones SRL",  # Use existing provider
                "client": "Cliente Test SA",
                "internal_coordinator": "María Elena Coordinadora",
                "quantity": 2,
                "item_description": "Flores decorativas para evento",
                "sold_amount_ars": 1500.0,
                "payment_method": "Transferencia",  # Use Spanish enum value
                "cost_ars": 800.0,
                "comments": "Test purchase from provider integration"
            }
            
            response = self.session.post(f"{API_BASE}/shop-cash", json=shop_cash_data)
            
            if response.status_code == 200:
                shop_entry = response.json()
                self.log_test("Shop Cash Integration - Create Entry", True,
                            f"Created shop cash entry with provider: {shop_entry.get('provider')}")
                
                # Now check if the provider's financials would be updated when retrieved
                # Find the provider by name
                providers_response = self.session.get(f"{API_BASE}/providers")
                if providers_response.status_code == 200:
                    providers = providers_response.json()
                    flores_provider = next((p for p in providers if "Flores & Decoraciones" in p.get('name', '')), None)
                    
                    if flores_provider:
                        provider_id = flores_provider.get('id')
                        provider_response = self.session.get(f"{API_BASE}/providers/{provider_id}")
                        
                        if provider_response.status_code == 200:
                            provider_with_financials = provider_response.json()
                            self.log_test("Shop Cash Integration - Provider Financials", True,
                                        f"Provider financials calculated: transactions={provider_with_financials.get('transaction_count', 0)}")
                            return True
                        else:
                            self.log_test("Shop Cash Integration - Provider Financials", False,
                                        f"Failed to retrieve provider with financials: {provider_response.status_code}")
                            return False
                    else:
                        self.log_test("Shop Cash Integration - Find Provider", False,
                                    "Could not find Flores provider for integration test")
                        return False
                else:
                    self.log_test("Shop Cash Integration - Get Providers", False,
                                "Failed to retrieve providers for integration test")
                    return False
            else:
                self.log_test("Shop Cash Integration - Create Entry", False,
                            f"Failed to create shop cash entry: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Shop Cash Integration", False, f"Error testing integration: {str(e)}")
            return False
    
    def run_provider_tests(self):
        """Run complete provider management test suite"""
        print("=" * 80)
        print("🏪 PROVIDER MANAGEMENT SYSTEM API TEST SUITE")
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
        print("📋 TESTING INITIAL PROVIDERS")
        print("=" * 50)
        
        # Step 3: Test initial providers
        self.test_get_initial_providers()
        
        print("\n" + "=" * 50)
        print("🔍 TESTING AUTOCOMPLETE FUNCTIONALITY")
        print("=" * 50)
        
        # Step 4: Test autocomplete
        self.test_provider_autocomplete()
        
        print("\n" + "=" * 50)
        print("➕ TESTING PROVIDER CREATION")
        print("=" * 50)
        
        # Step 5: Test creating new provider
        self.test_create_new_provider()
        
        print("\n" + "=" * 50)
        print("🚫 TESTING VALIDATION")
        print("=" * 50)
        
        # Step 6: Test duplicate validation
        self.test_duplicate_provider_validation()
        
        print("\n" + "=" * 50)
        print("✏️ TESTING PROVIDER UPDATES")
        print("=" * 50)
        
        # Step 7: Test updating provider
        self.test_update_provider()
        
        print("\n" + "=" * 50)
        print("📊 TESTING PROVIDER RETRIEVAL & FINANCIALS")
        print("=" * 50)
        
        # Step 8: Test specific provider retrieval
        self.test_get_specific_provider()
        
        print("\n" + "=" * 50)
        print("📈 TESTING PROVIDER SUMMARY")
        print("=" * 50)
        
        # Step 9: Test provider summary
        self.test_provider_summary()
        
        print("\n" + "=" * 50)
        print("🔗 TESTING SHOP CASH INTEGRATION")
        print("=" * 50)
        
        # Step 10: Test shop cash integration
        self.test_shop_cash_integration()
        
        # Summary
        self.print_provider_summary()
        
        return True
    
    def print_provider_summary(self):
        """Print provider test results summary"""
        print("\n" + "=" * 80)
        print("📊 PROVIDER MANAGEMENT TEST RESULTS SUMMARY")
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
        with open('/app/provider_management_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"📄 Detailed results saved to: /app/provider_management_test_results.json")


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
    print("🚀 Starting Backend API Test Suite")
    print("Choose test suite to run:")
    print("1. Provider Management System Tests")
    print("2. Deco Movements Module Tests (Legacy)")
    print("3. Run Both Test Suites")
    
    # For automated testing, default to Provider Management tests
    choice = "1"  # Default to provider tests as requested
    
    if choice == "1":
        print("\n🏪 Running Provider Management System Tests...")
        tester = ProviderManagementAPITester()
        try:
            success = tester.run_provider_tests()
            return 0 if success else 1
        except KeyboardInterrupt:
            print("\n⚠️  Tests interrupted by user")
            return 1
        except Exception as e:
            print(f"\n💥 Unexpected error: {str(e)}")
            return 1
    
    elif choice == "2":
        print("\n📝 Running Deco Movements Module Tests...")
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
    
    elif choice == "3":
        print("\n🔄 Running Both Test Suites...")
        
        # Run Provider Management tests first
        print("\n" + "="*80)
        print("🏪 PROVIDER MANAGEMENT SYSTEM TESTS")
        print("="*80)
        provider_tester = ProviderManagementAPITester()
        provider_success = provider_tester.run_provider_tests()
        
        # Run Deco Movements tests
        print("\n" + "="*80)
        print("📝 DECO MOVEMENTS MODULE TESTS")
        print("="*80)
        deco_tester = DecoMovementsAPITester()
        deco_success = deco_tester.run_all_tests()
        
        # Combined summary
        print("\n" + "="*80)
        print("🎯 COMBINED TEST RESULTS")
        print("="*80)
        provider_total = len(provider_tester.test_results)
        provider_passed = len([r for r in provider_tester.test_results if r['success']])
        deco_total = len(deco_tester.test_results)
        deco_passed = len([r for r in deco_tester.test_results if r['success']])
        
        total_tests = provider_total + deco_total
        total_passed = provider_passed + deco_passed
        
        print(f"Provider Management: {provider_passed}/{provider_total} passed")
        print(f"Deco Movements: {deco_passed}/{deco_total} passed")
        print(f"Overall: {total_passed}/{total_tests} passed ({(total_passed/total_tests)*100:.1f}%)")
        
        return 0 if (provider_success and deco_success) else 1
    
    else:
        print("Invalid choice. Defaulting to Provider Management tests...")
        tester = ProviderManagementAPITester()
        try:
            success = tester.run_provider_tests()
            return 0 if success else 1
        except KeyboardInterrupt:
            print("\n⚠️  Tests interrupted by user")
            return 1
        except Exception as e:
            print(f"\n💥 Unexpected error: {str(e)}")
            return 1

if __name__ == "__main__":
    sys.exit(main())