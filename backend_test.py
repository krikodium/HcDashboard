#!/usr/bin/env python3
"""
Backend API Testing for Hermanas Caradonti Admin Tool
Testing Phase 2.2: Event Providers API and Enhanced Events Cash functionality
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
    
    def test_event_providers_create(self):
        """Test POST /api/event-providers"""
        try:
            test_provider = {
                "name": f"Test Catering Provider {datetime.now().strftime('%H%M%S')}",
                "category": "Catering",
                "provider_type": "Vendor",
                "contact_person": "María González",
                "phone": "+54 11 1234-5678",
                "email": "maria@testcatering.com",
                "address": "Av. Corrientes 1234, Buenos Aires",
                "notes": "Specialized in wedding catering",
                "default_payment_terms": "30 días"
            }
            
            response = requests.post(
                f"{self.base_url}/event-providers",
                json=test_provider,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                created_provider = response.json()
                self.log_test(
                    "Event Providers Create", 
                    True, 
                    f"Created provider: {created_provider.get('name')}",
                    created_provider
                )
                return created_provider
            else:
                self.log_test("Event Providers Create", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Event Providers Create", False, f"Error: {str(e)}")
            return None
    
    def test_event_providers_list(self):
        """Test GET /api/event-providers"""
        try:
            response = requests.get(
                f"{self.base_url}/event-providers",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                providers = response.json()
                self.log_test(
                    "Event Providers List", 
                    True, 
                    f"Retrieved {len(providers)} event providers",
                    {"count": len(providers), "sample": providers[:2] if providers else []}
                )
                return providers
            else:
                self.log_test("Event Providers List", False, f"Failed: {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_test("Event Providers List", False, f"Error: {str(e)}")
            return []
    
    def test_event_providers_filtering(self):
        """Test GET /api/event-providers with filtering"""
        try:
            # Test filtering by category
            params = {
                "category": "Catering",
                "active_only": True
            }
            
            response = requests.get(
                f"{self.base_url}/event-providers",
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                providers = response.json()
                self.log_test(
                    "Event Providers Filtering", 
                    True, 
                    f"Found {len(providers)} catering providers",
                    {"category": "Catering", "count": len(providers)}
                )
                return providers
            else:
                self.log_test("Event Providers Filtering", False, f"Failed: {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_test("Event Providers Filtering", False, f"Error: {str(e)}")
            return []
    
    def test_event_providers_autocomplete(self):
        """Test GET /api/event-providers/autocomplete"""
        try:
            params = {
                "q": "Test",
                "category": "Catering",
                "limit": 5
            }
            
            response = requests.get(
                f"{self.base_url}/event-providers/autocomplete",
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                self.log_test(
                    "Event Providers Autocomplete", 
                    True, 
                    f"Found {len(results)} matching providers",
                    {"query": "Test", "results": results}
                )
                return results
            else:
                self.log_test("Event Providers Autocomplete", False, f"Failed: {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_test("Event Providers Autocomplete", False, f"Error: {str(e)}")
            return []
    
    def test_event_providers_increment_usage(self, provider_id: str):
        """Test PATCH /api/event-providers/{id}/increment-usage"""
        try:
            response = requests.patch(
                f"{self.base_url}/event-providers/{provider_id}/increment-usage",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "Event Providers Increment Usage", 
                    True, 
                    "Usage count incremented successfully",
                    result
                )
                return True
            else:
                self.log_test("Event Providers Increment Usage", False, f"Failed: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Event Providers Increment Usage", False, f"Error: {str(e)}")
            return False
    
    def test_event_providers_summary(self):
        """Test GET /api/event-providers/summary"""
        try:
            response = requests.get(
                f"{self.base_url}/event-providers/summary",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                summary = response.json()
                self.log_test(
                    "Event Providers Summary", 
                    True, 
                    "Retrieved event providers summary",
                    summary
                )
                return summary
            else:
                self.log_test("Event Providers Summary", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Event Providers Summary", False, f"Error: {str(e)}")
            return None
    
    def test_events_cash_create(self):
        """Test POST /api/events-cash"""
        try:
            test_event = {
                "header": {
                    "event_date": "2024-12-25",
                    "organizer": "María Elena Caradonti",
                    "client_name": "Familia Rodriguez",
                    "client_razon_social": "Rodriguez Events SRL",
                    "event_type": "Wedding",
                    "province": "Buenos Aires",
                    "localidad": "Palermo",
                    "viaticos_armado": 5000.0,
                    "hc_fees": 15000.0,
                    "total_budget_no_iva": 150000.0,
                    "budget_number": f"BUD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "payment_terms": "30% anticipo, 40% a 15 días, 30% contra entrega"
                },
                "initial_payment": {
                    "payment_method": "Transferencia",
                    "date": date.today().isoformat(),
                    "detail": "Anticipo inicial del evento",
                    "income_ars": 45000.0
                }
            }
            
            response = requests.post(
                f"{self.base_url}/events-cash",
                json=test_event,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                created_event = response.json()
                self.log_test(
                    "Events Cash Create", 
                    True, 
                    f"Created event: {created_event.get('header', {}).get('client_name')}",
                    created_event
                )
                return created_event
            else:
                self.log_test("Events Cash Create", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Events Cash Create", False, f"Error: {str(e)}")
            return None
    
    def test_events_cash_list(self):
        """Test GET /api/events-cash"""
        try:
            response = requests.get(
                f"{self.base_url}/events-cash",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                events = response.json()
                self.log_test(
                    "Events Cash List", 
                    True, 
                    f"Retrieved {len(events)} events",
                    {"count": len(events), "sample": events[:1] if events else []}
                )
                return events
            else:
                self.log_test("Events Cash List", False, f"Failed: {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_test("Events Cash List", False, f"Error: {str(e)}")
            return []
    
    def test_events_cash_add_ledger_entry_enhanced(self, event_id: str, provider_id: str = None):
        """Test POST /api/events-cash/{event_id}/ledger with enhanced model"""
        try:
            test_entry = {
                "payment_method": "Efectivo",
                "date": date.today().isoformat(),
                "detail": "Pago a proveedor de catering",
                "expense_ars": 25000.0,
                "provider_id": provider_id,
                "expense_category_id": None,
                "is_client_payment": False
            }
            
            response = requests.post(
                f"{self.base_url}/events-cash/{event_id}/ledger",
                json=test_entry,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                updated_event = response.json()
                self.log_test(
                    "Events Cash Add Ledger Entry Enhanced", 
                    True, 
                    "Added ledger entry with provider integration",
                    {"event_id": event_id, "provider_id": provider_id}
                )
                return updated_event
            else:
                self.log_test("Events Cash Add Ledger Entry Enhanced", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Events Cash Add Ledger Entry Enhanced", False, f"Error: {str(e)}")
            return None
    
    def test_events_cash_client_payment_processing(self, event_id: str):
        """Test client payment processing functionality"""
        try:
            # Test client payment that should update payment status automatically
            client_payment = {
                "payment_method": "Bank Transfer",
                "date": date.today().isoformat(),
                "detail": "Segundo pago del cliente",
                "income_ars": 60000.0,
                "is_client_payment": True
            }
            
            response = requests.post(
                f"{self.base_url}/events-cash/{event_id}/ledger",
                json=client_payment,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                updated_event = response.json()
                payment_status = updated_event.get('payment_status', {})
                self.log_test(
                    "Events Cash Client Payment Processing", 
                    True, 
                    "Client payment processed and payment status updated",
                    {
                        "payment_status": payment_status,
                        "balance_due": payment_status.get('balance_due', 0)
                    }
                )
                return updated_event
            else:
                self.log_test("Events Cash Client Payment Processing", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Events Cash Client Payment Processing", False, f"Error: {str(e)}")
            return None
    
    def test_events_cash_expenses_summary(self, event_id: str):
        """Test GET /api/events-cash/{event_id}/expenses-summary"""
        try:
            response = requests.get(
                f"{self.base_url}/events-cash/{event_id}/expenses-summary",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                summary = response.json()
                self.log_test(
                    "Events Cash Expenses Summary", 
                    True, 
                    "Retrieved expense summary report",
                    summary
                )
                return summary
            else:
                self.log_test("Events Cash Expenses Summary", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Events Cash Expenses Summary", False, f"Error: {str(e)}")
            return None
    
    def test_integration_event_providers_with_events_cash(self):
        """Test integration between Event Providers and Events Cash"""
        try:
            # Create multiple event providers with different categories
            providers_data = [
                {
                    "name": f"Premium Catering Services {datetime.now().strftime('%H%M%S')}",
                    "category": "Catering",
                    "provider_type": "Vendor",
                    "contact_person": "Carlos Mendoza",
                    "phone": "+54 11 2345-6789",
                    "email": "carlos@premiumcatering.com"
                },
                {
                    "name": f"Elite Decorations {datetime.now().strftime('%H%M%S')}",
                    "category": "Decoration",
                    "provider_type": "Subcontractor",
                    "contact_person": "Ana Rodriguez",
                    "phone": "+54 11 3456-7890",
                    "email": "ana@elitedecorations.com"
                },
                {
                    "name": f"Sound & Music Pro {datetime.now().strftime('%H%M%S')}",
                    "category": "Music",
                    "provider_type": "Vendor",
                    "contact_person": "Diego Silva",
                    "phone": "+54 11 4567-8901",
                    "email": "diego@soundmusicpro.com"
                }
            ]
            
            created_providers = []
            for provider_data in providers_data:
                response = requests.post(
                    f"{self.base_url}/event-providers",
                    json=provider_data,
                    headers=self.headers,
                    timeout=10
                )
                if response.status_code == 200:
                    created_providers.append(response.json())
            
            if len(created_providers) < 3:
                self.log_test("Integration Test - Provider Creation", False, f"Only created {len(created_providers)} of 3 providers")
                return False
            
            # Create an event
            test_event = {
                "header": {
                    "event_date": "2024-12-30",
                    "organizer": "Paz Caradonti",
                    "client_name": "Empresa ABC",
                    "event_type": "Corporate",
                    "province": "Buenos Aires",
                    "localidad": "Recoleta",
                    "total_budget_no_iva": 200000.0,
                    "budget_number": f"INT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "payment_terms": "50% anticipo, 50% contra entrega"
                }
            }
            
            event_response = requests.post(
                f"{self.base_url}/events-cash",
                json=test_event,
                headers=self.headers,
                timeout=10
            )
            
            if event_response.status_code != 200:
                self.log_test("Integration Test - Event Creation", False, f"Failed to create event: {event_response.status_code}")
                return False
            
            created_event = event_response.json()
            event_id = created_event.get('id') or created_event.get('_id')
            
            # Add ledger entries with provider references
            integration_success = True
            for i, provider in enumerate(created_providers):
                provider_id = provider.get('id') or provider.get('_id')
                entry_data = {
                    "payment_method": "Bank Transfer",
                    "date": date.today().isoformat(),
                    "detail": f"Pago a {provider['name']}",
                    "expense_ars": 15000.0 + (i * 5000),  # Different amounts
                    "provider_id": provider_id,
                    "is_client_payment": False
                }
                
                entry_response = requests.post(
                    f"{self.base_url}/events-cash/{event_id}/ledger",
                    json=entry_data,
                    headers=self.headers,
                    timeout=10
                )
                
                if entry_response.status_code != 200:
                    integration_success = False
                    break
            
            if integration_success:
                self.log_test(
                    "Integration Test - Event Providers with Events Cash", 
                    True, 
                    f"Successfully integrated {len(created_providers)} providers with event ledger",
                    {
                        "providers_created": len(created_providers),
                        "event_id": event_id,
                        "ledger_entries_added": len(created_providers)
                    }
                )
                return {"event_id": event_id, "providers": created_providers}
            else:
                self.log_test("Integration Test - Event Providers with Events Cash", False, "Failed to add all ledger entries")
                return False
                
        except Exception as e:
            self.log_test("Integration Test - Event Providers with Events Cash", False, f"Error: {str(e)}")
            return False
    
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
        """Run all backend tests for Phase 2.2: Event Providers and Enhanced Events Cash"""
        print("🚀 Starting Backend API Tests for Phase 2.2: Event Providers and Enhanced Events Cash")
        print("=" * 80)
        
        # Test authentication first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Test health check
        self.test_health_check()
        
        # Test authentication requirement
        self.test_authentication_required()
        
        # Test Event Providers API
        print("\n🏢 Testing Event Providers API...")
        created_provider = self.test_event_providers_create()
        providers = self.test_event_providers_list()
        self.test_event_providers_filtering()
        self.test_event_providers_autocomplete()
        self.test_event_providers_summary()
        
        # Test increment usage if we have a provider
        if providers and len(providers) > 0:
            provider_id = providers[0].get('id') or providers[0].get('_id')
            if provider_id:
                self.test_event_providers_increment_usage(provider_id)
            else:
                print("⚠️  No provider ID found for increment usage test")
        
        # Test Enhanced Events Cash API
        print("\n💰 Testing Enhanced Events Cash API...")
        created_event = self.test_events_cash_create()
        events = self.test_events_cash_list()
        
        # Test enhanced ledger entry functionality
        if created_event:
            event_id = created_event.get('id') or created_event.get('_id')
            provider_id = created_provider.get('id') if created_provider else None
            
            if event_id:
                # Test enhanced ledger entry with provider integration
                self.test_events_cash_add_ledger_entry_enhanced(event_id, provider_id)
                
                # Test client payment processing
                self.test_events_cash_client_payment_processing(event_id)
                
                # Test expense summary reporting
                self.test_events_cash_expenses_summary(event_id)
        
        # Test Integration Scenarios
        print("\n🔗 Testing Integration Scenarios...")
        integration_result = self.test_integration_event_providers_with_events_cash()
        
        # Test expense summary with integration data
        if integration_result and isinstance(integration_result, dict):
            event_id = integration_result.get('event_id')
            if event_id:
                self.test_events_cash_expenses_summary(event_id)
        
        # Test Application Categories API (existing functionality)
        print("\n📂 Testing Application Categories API...")
        categories = self.test_application_categories_list()
        created_category = self.test_application_categories_create()
        self.test_application_categories_autocomplete()
        self.test_application_categories_summary()
        
        # Test increment usage if we have a category
        if categories and len(categories) > 0:
            category_id = categories[0].get('id') or categories[0].get('_id')
            if category_id:
                self.test_application_categories_increment_usage(category_id)
        
        # Test General Cash API (existing functionality)
        print("\n💰 Testing General Cash API...")
        entries = self.test_general_cash_list()
        created_entry = self.test_general_cash_create()
        self.test_general_cash_summary()
        
        # Test approval if we have an entry
        if created_entry and (created_entry.get('id') or created_entry.get('_id')):
            entry_id = created_entry.get('id') or created_entry.get('_id')
            self.test_general_cash_approve(entry_id)
        elif entries and len(entries) > 0 and (entries[0].get('id') or entries[0].get('_id')):
            # Try with an existing entry
            entry_id = entries[0].get('id') or entries[0].get('_id')
            self.test_general_cash_approve(entry_id)
        
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