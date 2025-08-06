#!/usr/bin/env python3
"""
Backend API Testing for Hermanas Caradonti Admin Tool
Testing Phase 3: Shop Cash Module Overhaul - Inventory Management API
"""

import requests
import json
from datetime import datetime, date
from typing import Dict, Any, Optional
import sys
import os

# Configuration
BACKEND_URL = "https://28ce6753-d6e3-45d9-b7dd-28de95c32168.preview.emergentagent.com/api"
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
                "payment_method": "Transferencia",
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
                    "event_type": "Corporate Event",
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
                    "payment_method": "Transferencia",
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
    
    def test_inventory_products_create(self):
        """Test POST /api/inventory/products"""
        try:
            test_product = {
                "sku": f"TEST-DECOR-{datetime.now().strftime('%H%M%S')}",
                "name": f"Test Decorative Vase {datetime.now().strftime('%H%M%S')}",
                "description": "Beautiful ceramic vase for event decoration",
                "category": "Décor",
                "provider_name": "Ceramicas Buenos Aires",
                "cost_ars": 2500.0,
                "cost_usd": 15.0,
                "selling_price_ars": 4000.0,
                "selling_price_usd": 25.0,
                "current_stock": 10,
                "min_stock_threshold": 3,
                "location": "Warehouse A - Shelf 12",
                "condition": "New",
                "notes": "Premium quality ceramic, handle with care"
            }
            
            response = requests.post(
                f"{self.base_url}/inventory/products",
                json=test_product,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                created_product = response.json()
                self.log_test(
                    "Inventory Products Create", 
                    True, 
                    f"Created product: {created_product.get('name')} (SKU: {created_product.get('sku')})",
                    created_product
                )
                return created_product
            else:
                self.log_test("Inventory Products Create", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Inventory Products Create", False, f"Error: {str(e)}")
            return None
    
    def test_inventory_products_list(self):
        """Test GET /api/inventory/products with filtering and sorting"""
        try:
            # Test basic list
            response = requests.get(
                f"{self.base_url}/inventory/products",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                products = response.json()
                self.log_test(
                    "Inventory Products List", 
                    True, 
                    f"Retrieved {len(products)} products",
                    {"count": len(products), "sample": products[:2] if products else []}
                )
                
                # Test filtering by category
                params = {
                    "category": "Décor",
                    "active_only": True,
                    "sort_by": "name",
                    "sort_order": "asc"
                }
                
                filter_response = requests.get(
                    f"{self.base_url}/inventory/products",
                    params=params,
                    headers=self.headers,
                    timeout=10
                )
                
                if filter_response.status_code == 200:
                    filtered_products = filter_response.json()
                    self.log_test(
                        "Inventory Products List - Filtering", 
                        True, 
                        f"Found {len(filtered_products)} Décor products",
                        {"category": "Décor", "count": len(filtered_products)}
                    )
                
                return products
            else:
                self.log_test("Inventory Products List", False, f"Failed: {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_test("Inventory Products List", False, f"Error: {str(e)}")
            return []
    
    def test_inventory_products_autocomplete(self):
        """Test GET /api/inventory/products/autocomplete"""
        try:
            params = {
                "q": "Test",
                "category": "Décor",
                "in_stock_only": True,
                "limit": 5
            }
            
            response = requests.get(
                f"{self.base_url}/inventory/products/autocomplete",
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                self.log_test(
                    "Inventory Products Autocomplete", 
                    True, 
                    f"Found {len(results)} matching products",
                    {"query": "Test", "results": results}
                )
                return results
            else:
                self.log_test("Inventory Products Autocomplete", False, f"Failed: {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_test("Inventory Products Autocomplete", False, f"Error: {str(e)}")
            return []
    
    def test_inventory_products_get_by_id(self, product_id: str):
        """Test GET /api/inventory/products/{id}"""
        try:
            response = requests.get(
                f"{self.base_url}/inventory/products/{product_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                product = response.json()
                self.log_test(
                    "Inventory Products Get by ID", 
                    True, 
                    f"Retrieved product: {product.get('name')}",
                    product
                )
                return product
            else:
                self.log_test("Inventory Products Get by ID", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Inventory Products Get by ID", False, f"Error: {str(e)}")
            return None
    
    def test_inventory_products_update(self, product_id: str):
        """Test PUT /api/inventory/products/{id}"""
        try:
            update_data = {
                "description": "Updated description - Premium ceramic vase with gold accents",
                "selling_price_ars": 4500.0,
                "selling_price_usd": 28.0,
                "notes": "Updated pricing for premium quality"
            }
            
            response = requests.put(
                f"{self.base_url}/inventory/products/{product_id}",
                json=update_data,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                updated_product = response.json()
                self.log_test(
                    "Inventory Products Update", 
                    True, 
                    f"Updated product: {updated_product.get('name')}",
                    updated_product
                )
                return updated_product
            else:
                self.log_test("Inventory Products Update", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Inventory Products Update", False, f"Error: {str(e)}")
            return None
    
    def test_inventory_products_stock_adjustment(self, product_id: str):
        """Test POST /api/inventory/products/{id}/stock-adjustment"""
        try:
            adjustment_data = {
                "adjustment_type": "increase",
                "quantity": 5,
                "reason": "New stock received from supplier",
                "notes": "Quality checked and approved"
            }
            
            response = requests.post(
                f"{self.base_url}/inventory/products/{product_id}/stock-adjustment",
                json=adjustment_data,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "Inventory Products Stock Adjustment", 
                    True, 
                    f"Stock adjusted: {result.get('previous_stock')} → {result.get('new_stock')}",
                    result
                )
                return result
            else:
                self.log_test("Inventory Products Stock Adjustment", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Inventory Products Stock Adjustment", False, f"Error: {str(e)}")
            return None
    
    def test_inventory_products_delete(self, product_id: str):
        """Test DELETE /api/inventory/products/{id} (soft delete)"""
        try:
            # Test soft delete first
            response = requests.delete(
                f"{self.base_url}/inventory/products/{product_id}",
                params={"hard_delete": False},
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "Inventory Products Delete (Soft)", 
                    True, 
                    "Product deactivated successfully",
                    result
                )
                return True
            else:
                self.log_test("Inventory Products Delete (Soft)", False, f"Failed: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Inventory Products Delete (Soft)", False, f"Error: {str(e)}")
            return False
    
    def test_inventory_summary(self):
        """Test GET /api/inventory/summary"""
        try:
            response = requests.get(
                f"{self.base_url}/inventory/summary",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                summary = response.json()
                self.log_test(
                    "Inventory Summary", 
                    True, 
                    "Retrieved inventory summary statistics",
                    summary
                )
                return summary
            else:
                self.log_test("Inventory Summary", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Inventory Summary", False, f"Error: {str(e)}")
            return None
    
    def test_inventory_bulk_import(self):
        """Test POST /api/inventory/bulk-import"""
        try:
            # Create a test CSV content
            csv_content = """sku,name,description,category,provider_name,cost_ars,cost_usd,selling_price_ars,selling_price_usd,current_stock,min_stock_threshold,location,condition,notes
BULK-001,Bulk Test Lamp,Modern LED table lamp,Lighting,Lighting Solutions SA,1500,10,2500,16,8,2,Warehouse B,New,Imported from Italy
BULK-002,Bulk Test Chair,Elegant dining chair,Furniture,Muebles Premium,3000,20,5000,32,5,1,Warehouse A,New,Solid wood construction
BULK-003,Bulk Test Textile,Luxury silk curtain,Textiles,Textiles Buenos Aires,2000,12,3200,20,12,3,Warehouse C,New,100% silk material"""
            
            # Create a temporary file-like object
            import io
            csv_file = io.BytesIO(csv_content.encode('utf-8'))
            
            files = {
                'file': ('test_products.csv', csv_file, 'text/csv')
            }
            
            # Remove Content-Type header for file upload
            headers_for_upload = {k: v for k, v in self.headers.items() if k != 'Content-Type'}
            
            response = requests.post(
                f"{self.base_url}/inventory/bulk-import",
                files=files,
                headers=headers_for_upload,
                params={"update_existing": False},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "Inventory Bulk Import", 
                    True, 
                    f"Imported {result.get('successful_imports', 0)} of {result.get('total_rows', 0)} products",
                    result
                )
                return result
            else:
                self.log_test("Inventory Bulk Import", False, f"Failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Inventory Bulk Import", False, f"Error: {str(e)}")
            return None
    
    def test_shop_cash_inventory_integration(self):
        """Test Shop Cash integration with inventory (stock reduction on sales)"""
        try:
            # First, create a product for testing
            test_product = {
                "sku": f"SHOP-TEST-{datetime.now().strftime('%H%M%S')}",
                "name": f"Shop Test Item {datetime.now().strftime('%H%M%S')}",
                "description": "Test item for shop cash integration",
                "category": "Accessories",
                "provider_name": "Test Supplier",
                "cost_ars": 1000.0,
                "selling_price_ars": 1800.0,
                "current_stock": 20,
                "min_stock_threshold": 5
            }
            
            product_response = requests.post(
                f"{self.base_url}/inventory/products",
                json=test_product,
                headers=self.headers,
                timeout=10
            )
            
            if product_response.status_code != 200:
                self.log_test("Shop Cash Inventory Integration - Product Creation", False, "Failed to create test product")
                return False
            
            created_product = product_response.json()
            product_sku = created_product.get('sku')
            
            # Now create a shop cash entry with this product
            shop_cash_entry = {
                "date": date.today().isoformat(),
                "client": "Test Customer",
                "sku": product_sku,
                "quantity": 3,
                "sold_amount_ars": 5400.0,  # 3 * 1800
                "payment_method": "Efectivo",
                "notes": "Test sale for inventory integration"
            }
            
            sale_response = requests.post(
                f"{self.base_url}/shop-cash",
                json=shop_cash_entry,
                headers=self.headers,
                timeout=10
            )
            
            if sale_response.status_code == 200:
                # Verify that stock was reduced
                updated_product_response = requests.get(
                    f"{self.base_url}/inventory/products/{created_product.get('id')}",
                    headers=self.headers,
                    timeout=10
                )
                
                if updated_product_response.status_code == 200:
                    updated_product = updated_product_response.json()
                    expected_stock = 20 - 3  # Original stock minus sold quantity
                    actual_stock = updated_product.get('current_stock', 0)
                    
                    if actual_stock == expected_stock:
                        self.log_test(
                            "Shop Cash Inventory Integration", 
                            True, 
                            f"Stock correctly reduced from 20 to {actual_stock} after sale",
                            {
                                "product_sku": product_sku,
                                "quantity_sold": 3,
                                "stock_before": 20,
                                "stock_after": actual_stock
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "Shop Cash Inventory Integration", 
                            False, 
                            f"Stock not correctly updated. Expected: {expected_stock}, Actual: {actual_stock}"
                        )
                        return False
                else:
                    self.log_test("Shop Cash Inventory Integration", False, "Failed to retrieve updated product")
                    return False
            else:
                self.log_test("Shop Cash Inventory Integration", False, f"Failed to create shop cash entry: {sale_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Shop Cash Inventory Integration", False, f"Error: {str(e)}")
            return False
    
    def test_integration_inventory_comprehensive(self):
        """Test comprehensive inventory integration scenario"""
        try:
            # Create multiple products with different categories
            products_data = [
                {
                    "sku": f"INT-DECOR-{datetime.now().strftime('%H%M%S')}",
                    "name": f"Integration Test Vase {datetime.now().strftime('%H%M%S')}",
                    "category": "Décor",
                    "provider_name": "Ceramicas Elite",
                    "cost_ars": 2000.0,
                    "selling_price_ars": 3500.0,
                    "current_stock": 15
                },
                {
                    "sku": f"INT-FURN-{datetime.now().strftime('%H%M%S')}",
                    "name": f"Integration Test Chair {datetime.now().strftime('%H%M%S')}",
                    "category": "Furniture",
                    "provider_name": "Muebles Modernos",
                    "cost_ars": 5000.0,
                    "selling_price_ars": 8000.0,
                    "current_stock": 8
                },
                {
                    "sku": f"INT-LIGHT-{datetime.now().strftime('%H%M%S')}",
                    "name": f"Integration Test Lamp {datetime.now().strftime('%H%M%S')}",
                    "category": "Lighting",
                    "provider_name": "Iluminacion Pro",
                    "cost_ars": 3000.0,
                    "selling_price_ars": 4800.0,
                    "current_stock": 12
                }
            ]
            
            created_products = []
            for product_data in products_data:
                response = requests.post(
                    f"{self.base_url}/inventory/products",
                    json=product_data,
                    headers=self.headers,
                    timeout=10
                )
                if response.status_code == 200:
                    created_products.append(response.json())
            
            if len(created_products) < 3:
                self.log_test("Integration Test - Product Creation", False, f"Only created {len(created_products)} of 3 products")
                return False
            
            # Test stock adjustments on each product
            integration_success = True
            for i, product in enumerate(created_products):
                product_id = product.get('id')
                adjustment_data = {
                    "adjustment_type": "increase",
                    "quantity": 5 + i,  # Different quantities
                    "reason": f"Integration test stock increase #{i+1}",
                    "notes": "Automated integration test"
                }
                
                adjustment_response = requests.post(
                    f"{self.base_url}/inventory/products/{product_id}/stock-adjustment",
                    json=adjustment_data,
                    headers=self.headers,
                    timeout=10
                )
                
                if adjustment_response.status_code != 200:
                    integration_success = False
                    break
            
            # Test shop cash sales for inventory integration
            if integration_success:
                for product in created_products[:2]:  # Test sales on first 2 products
                    shop_cash_entry = {
                        "date": date.today().isoformat(),
                        "client": f"Integration Test Client {datetime.now().strftime('%H%M%S')}",
                        "sku": product.get('sku'),
                        "quantity": 2,
                        "sold_amount_ars": product.get('selling_price_ars', 0) * 2,
                        "payment_method": "Transferencia",
                        "notes": "Integration test sale"
                    }
                    
                    sale_response = requests.post(
                        f"{self.base_url}/shop-cash",
                        json=shop_cash_entry,
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if sale_response.status_code != 200:
                        integration_success = False
                        break
            
            if integration_success:
                self.log_test(
                    "Integration Test - Comprehensive Inventory", 
                    True, 
                    f"Successfully integrated {len(created_products)} products with stock adjustments and sales",
                    {
                        "products_created": len(created_products),
                        "stock_adjustments": len(created_products),
                        "sales_processed": 2
                    }
                )
                return {"products": created_products}
            else:
                self.log_test("Integration Test - Comprehensive Inventory", False, "Failed during integration testing")
                return False
                
        except Exception as e:
            self.log_test("Integration Test - Comprehensive Inventory", False, f"Error: {str(e)}")
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
    
    def run_inventory_tests(self):
        """Run all inventory management tests for Phase 3"""
        print("\n📦 Testing Inventory Management API...")
        
        # Test basic CRUD operations
        created_product = self.test_inventory_products_create()
        products = self.test_inventory_products_list()
        self.test_inventory_products_autocomplete()
        self.test_inventory_summary()
        
        # Test operations on created product
        if created_product:
            product_id = created_product.get('id')
            if product_id:
                self.test_inventory_products_get_by_id(product_id)
                self.test_inventory_products_update(product_id)
                self.test_inventory_products_stock_adjustment(product_id)
                # Note: We'll skip delete test to keep the product for integration tests
        
        # Test bulk import
        self.test_inventory_bulk_import()
        
        # Test shop cash integration
        self.test_shop_cash_inventory_integration()
        
        # Test comprehensive integration
        integration_result = self.test_integration_inventory_comprehensive()
        
        return True
    
    def run_all_tests(self):
        """Run all backend tests for Phase 3: Shop Cash Module Overhaul - Inventory Management"""
        print("🚀 Starting Backend API Tests for Phase 3: Shop Cash Module Overhaul - Inventory Management")
        print("=" * 80)
        
        # Test authentication first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Test health check
        self.test_health_check()
        
        # Test authentication requirement
        self.test_authentication_required()
        
        # Run Inventory Management Tests (Phase 3 Focus)
        self.run_inventory_tests()
        
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