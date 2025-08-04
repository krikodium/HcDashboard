#!/usr/bin/env python3
"""
Events Cash Module Critical Bug Test Suite
Focus: Database persistence and running balance calculation issues

This test suite specifically targets the reported critical bug:
- New ledger entries disappear after page refresh
- Running balance doesn't update correctly
- Database persistence issues with event_id matching

Test Flow:
1. Login with credentials (username: "mateo", password: "prueba123")
2. Create a new event using POST /api/events-cash
3. Add ledger entries using POST /api/events-cash/{event_id}/ledger
4. Verify ledger entries are saved and running balance updates
5. Retrieve event again to verify data persists
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

class EventsCashBugTester:
    def __init__(self):
        self.auth_token = None
        self.session = requests.Session()
        self.test_results = []
        self.created_event_id = None
        
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
    
    def create_test_event(self) -> Dict[str, Any]:
        """Create a test event with realistic data"""
        try:
            event_data = {
                "header": {
                    "event_date": "2024-03-15",
                    "organizer": "María González",
                    "client_name": "Familia Rodríguez",
                    "client_razon_social": "Eventos Rodríguez SRL",
                    "event_type": "Wedding",
                    "province": "Buenos Aires",
                    "localidad": "San Isidro",
                    "viaticos_armado": 15000.0,
                    "hc_fees": 25000.0,
                    "total_budget_no_iva": 450000.0,
                    "budget_number": "WED-2024-001",
                    "payment_terms": "30% anticipo, 40% 15 días antes del evento, 30% día del evento"
                },
                "initial_payment": {
                    "payment_method": "Transferencia",
                    "date": "2024-02-01",
                    "detail": "Anticipo inicial - 30% del presupuesto",
                    "income_ars": 135000.0
                }
            }
            
            response = self.session.post(f"{API_BASE}/events-cash", json=event_data)
            
            if response.status_code == 200:
                event = response.json()
                print(f"DEBUG: Event response: {json.dumps(event, indent=2, default=str)}")
                self.created_event_id = event.get("id")
                if not self.created_event_id:
                    # Try alternative ID fields
                    self.created_event_id = event.get("_id") or event.get("event_id")
                
                self.log_test("Create Event", True, 
                            f"Created event for {event_data['header']['client_name']} - ID: {self.created_event_id}")
                
                # Verify initial payment was processed
                if event.get("ledger_entries") and len(event["ledger_entries"]) > 0:
                    initial_entry = event["ledger_entries"][0]
                    if initial_entry.get("income_ars") == 135000.0:
                        self.log_test("Initial Payment Processing", True, 
                                    f"Initial payment of ARS 135,000 correctly processed")
                    else:
                        self.log_test("Initial Payment Processing", False, 
                                    f"Initial payment amount mismatch: expected 135000, got {initial_entry.get('income_ars')}")
                else:
                    self.log_test("Initial Payment Processing", False, "No ledger entries found in created event")
                
                return event
            else:
                self.log_test("Create Event", False, 
                            f"Failed to create event: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Create Event", False, f"Error creating event: {str(e)}")
            return None
    
    def add_ledger_entries(self) -> List[Dict[str, Any]]:
        """Add multiple ledger entries to test persistence"""
        if not self.created_event_id:
            self.log_test("Add Ledger Entries", False, "No event ID available")
            return []
        
        ledger_entries_data = [
            {
                "payment_method": "Efectivo",
                "date": "2024-02-15",
                "detail": "Compra de flores y decoración",
                "expense_ars": 45000.0
            },
            {
                "payment_method": "Transferencia", 
                "date": "2024-02-20",
                "detail": "Segundo pago del cliente - 40%",
                "income_ars": 180000.0
            },
            {
                "payment_method": "Tarjeta",
                "date": "2024-02-25", 
                "detail": "Pago a proveedor de catering",
                "expense_ars": 85000.0
            },
            {
                "payment_method": "Efectivo",
                "date": "2024-03-01",
                "detail": "Gastos varios de montaje",
                "expense_ars": 12000.0
            }
        ]
        
        added_entries = []
        
        for i, entry_data in enumerate(ledger_entries_data):
            try:
                # CRITICAL: Test the exact endpoint that's failing
                response = self.session.post(
                    f"{API_BASE}/events-cash/{self.created_event_id}/ledger", 
                    json=entry_data
                )
                
                if response.status_code == 200:
                    updated_event = response.json()
                    added_entries.append(entry_data)
                    
                    # Verify the entry was actually added
                    ledger_count = len(updated_event.get("ledger_entries", []))
                    expected_count = i + 2  # +1 for initial payment, +1 for current entry
                    
                    if ledger_count == expected_count:
                        self.log_test(f"Add Ledger Entry {i+1}", True, 
                                    f"Entry added successfully - Total entries: {ledger_count}")
                        
                        # Verify running balance calculation
                        latest_entry = updated_event["ledger_entries"][-1]
                        running_balance = latest_entry.get("running_balance_ars", 0)
                        self.log_test(f"Running Balance Check {i+1}", True, 
                                    f"Running balance ARS: {running_balance}")
                    else:
                        self.log_test(f"Add Ledger Entry {i+1}", False, 
                                    f"Entry count mismatch: expected {expected_count}, got {ledger_count}")
                else:
                    self.log_test(f"Add Ledger Entry {i+1}", False, 
                                f"Failed to add entry: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test(f"Add Ledger Entry {i+1}", False, f"Error adding entry: {str(e)}")
        
        return added_entries
    
    def verify_data_persistence(self) -> bool:
        """Critical test: Verify data persists by retrieving the event again"""
        if not self.created_event_id:
            self.log_test("Data Persistence Check", False, "No event ID available")
            return False
        
        try:
            # Retrieve the event again to simulate page refresh
            response = self.session.get(f"{API_BASE}/events-cash")
            
            if response.status_code == 200:
                events = response.json()
                print(f"DEBUG: Retrieved {len(events)} events")
                for i, event in enumerate(events):
                    print(f"DEBUG: Event {i}: ID={event.get('id')}, _ID={event.get('_id')}")
                
                # Find our created event
                our_event = None
                for event in events:
                    event_id = event.get("id") or event.get("_id")
                    if event_id == self.created_event_id:
                        our_event = event
                        break
                
                if our_event:
                    ledger_entries = our_event.get("ledger_entries", [])
                    entry_count = len(ledger_entries)
                    
                    # We expect 5 entries: 1 initial + 4 added
                    expected_count = 5
                    
                    if entry_count == expected_count:
                        self.log_test("Data Persistence Check", True, 
                                    f"All {entry_count} ledger entries persisted correctly")
                        
                        # Verify running balances are calculated correctly
                        final_entry = ledger_entries[-1]
                        final_balance = final_entry.get("running_balance_ars", 0)
                        
                        # Calculate expected balance manually
                        # Initial: +135,000, Entry1: -45,000, Entry2: +180,000, Entry3: -85,000, Entry4: -12,000
                        # Expected: 135,000 - 45,000 + 180,000 - 85,000 - 12,000 = 173,000
                        expected_balance = 173000.0
                        
                        if abs(final_balance - expected_balance) < 0.01:  # Allow for floating point precision
                            self.log_test("Running Balance Calculation", True, 
                                        f"Final running balance correct: ARS {final_balance}")
                        else:
                            self.log_test("Running Balance Calculation", False, 
                                        f"Balance mismatch: expected {expected_balance}, got {final_balance}")
                        
                        return True
                    else:
                        self.log_test("Data Persistence Check", False, 
                                    f"Entry count mismatch after retrieval: expected {expected_count}, got {entry_count}")
                        
                        # Log the actual entries for debugging
                        self.log_test("Debug - Retrieved Entries", False, 
                                    f"Retrieved entries", ledger_entries)
                        return False
                else:
                    self.log_test("Data Persistence Check", False, 
                                f"Event with ID {self.created_event_id} not found in retrieved events")
                    return False
            else:
                self.log_test("Data Persistence Check", False, 
                            f"Failed to retrieve events: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Data Persistence Check", False, f"Error checking persistence: {str(e)}")
            return False
    
    def test_event_id_consistency(self) -> bool:
        """Test if event_id used in API path matches database storage"""
        if not self.created_event_id:
            self.log_test("Event ID Consistency", False, "No event ID available")
            return False
        
        try:
            # Try to retrieve the specific event by ID (if endpoint exists)
            # First, let's check what's actually stored in the database by getting all events
            response = self.session.get(f"{API_BASE}/events-cash")
            
            if response.status_code == 200:
                events = response.json()
                
                # Check if our event ID exists and matches
                event_ids = [event.get("id") for event in events]
                
                if self.created_event_id in event_ids:
                    self.log_test("Event ID Consistency", True, 
                                f"Event ID {self.created_event_id} found in database")
                    
                    # Additional check: verify the ID format and structure
                    if len(self.created_event_id) == 36 and self.created_event_id.count('-') == 4:
                        self.log_test("Event ID Format", True, "Event ID follows UUID format")
                    else:
                        self.log_test("Event ID Format", False, 
                                    f"Event ID format unexpected: {self.created_event_id}")
                    
                    return True
                else:
                    self.log_test("Event ID Consistency", False, 
                                f"Event ID {self.created_event_id} not found in database. Available IDs: {event_ids}")
                    return False
            else:
                self.log_test("Event ID Consistency", False, 
                            f"Failed to retrieve events for ID check: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Event ID Consistency", False, f"Error checking event ID: {str(e)}")
            return False
    
    def test_database_update_operation(self) -> bool:
        """Test if update operations find and modify the correct document"""
        if not self.created_event_id:
            self.log_test("Database Update Operation", False, "No event ID available")
            return False
        
        try:
            # Add one more entry to test update operation
            test_entry = {
                "payment_method": "Transferencia",
                "date": "2024-03-10",
                "detail": "Test entry for update operation verification",
                "income_ars": 50000.0
            }
            
            # Get current state
            response_before = self.session.get(f"{API_BASE}/events-cash")
            events_before = response_before.json() if response_before.status_code == 200 else []
            our_event_before = None
            for event in events_before:
                if event.get("id") == self.created_event_id:
                    our_event_before = event
                    break
            
            if not our_event_before:
                self.log_test("Database Update Operation", False, "Could not find event before update")
                return False
            
            entries_before = len(our_event_before.get("ledger_entries", []))
            
            # Perform update
            response = self.session.post(
                f"{API_BASE}/events-cash/{self.created_event_id}/ledger", 
                json=test_entry
            )
            
            if response.status_code == 200:
                # Verify update worked by retrieving again
                response_after = self.session.get(f"{API_BASE}/events-cash")
                events_after = response_after.json() if response_after.status_code == 200 else []
                our_event_after = None
                for event in events_after:
                    if event.get("id") == self.created_event_id:
                        our_event_after = event
                        break
                
                if our_event_after:
                    entries_after = len(our_event_after.get("ledger_entries", []))
                    
                    if entries_after == entries_before + 1:
                        self.log_test("Database Update Operation", True, 
                                    f"Update operation successful: {entries_before} -> {entries_after} entries")
                        
                        # Verify the new entry is actually there
                        latest_entry = our_event_after["ledger_entries"][-1]
                        if latest_entry.get("detail") == test_entry["detail"]:
                            self.log_test("Update Content Verification", True, 
                                        "New entry content matches what was sent")
                        else:
                            self.log_test("Update Content Verification", False, 
                                        f"Entry content mismatch: expected '{test_entry['detail']}', got '{latest_entry.get('detail')}'")
                        
                        return True
                    else:
                        self.log_test("Database Update Operation", False, 
                                    f"Entry count didn't increase: {entries_before} -> {entries_after}")
                        return False
                else:
                    self.log_test("Database Update Operation", False, 
                                "Could not find event after update")
                    return False
            else:
                self.log_test("Database Update Operation", False, 
                            f"Update request failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Database Update Operation", False, f"Error testing update: {str(e)}")
            return False
    
    def run_critical_bug_tests(self):
        """Run the complete critical bug test suite"""
        print("=" * 80)
        print("🐛 EVENTS CASH MODULE - CRITICAL BUG TEST SUITE")
        print("=" * 80)
        print(f"Testing against: {API_BASE}")
        print("Focus: Database persistence and running balance calculation issues")
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed - aborting tests")
            return False
        
        print("\n" + "=" * 60)
        print("📝 STEP 1: CREATE TEST EVENT")
        print("=" * 60)
        
        # Step 2: Create test event
        event = self.create_test_event()
        if not event:
            print("❌ Event creation failed - aborting tests")
            return False
        
        print("\n" + "=" * 60)
        print("📋 STEP 2: ADD LEDGER ENTRIES")
        print("=" * 60)
        
        # Step 3: Add ledger entries
        added_entries = self.add_ledger_entries()
        
        print("\n" + "=" * 60)
        print("🔍 STEP 3: VERIFY DATA PERSISTENCE")
        print("=" * 60)
        
        # Step 4: Critical test - verify persistence
        persistence_ok = self.verify_data_persistence()
        
        print("\n" + "=" * 60)
        print("🆔 STEP 4: TEST EVENT ID CONSISTENCY")
        print("=" * 60)
        
        # Step 5: Test event ID consistency
        id_consistency_ok = self.test_event_id_consistency()
        
        print("\n" + "=" * 60)
        print("💾 STEP 5: TEST DATABASE UPDATE OPERATIONS")
        print("=" * 60)
        
        # Step 6: Test database update operations
        update_ok = self.test_database_update_operation()
        
        # Summary
        self.print_critical_bug_summary()
        
        return persistence_ok and id_consistency_ok and update_ok
    
    def print_critical_bug_summary(self):
        """Print critical bug test results summary"""
        print("\n" + "=" * 80)
        print("🐛 CRITICAL BUG TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Critical issues analysis
        critical_issues = []
        
        for result in self.test_results:
            if not result['success']:
                if "persistence" in result['test'].lower():
                    critical_issues.append("🚨 CRITICAL: Data persistence failure - entries disappear after refresh")
                elif "running balance" in result['test'].lower():
                    critical_issues.append("🚨 CRITICAL: Running balance calculation error")
                elif "event id" in result['test'].lower():
                    critical_issues.append("🚨 CRITICAL: Event ID consistency issue - API path doesn't match database")
                elif "update operation" in result['test'].lower():
                    critical_issues.append("🚨 CRITICAL: Database update operation failure")
        
        if critical_issues:
            print("\n🚨 CRITICAL ISSUES IDENTIFIED:")
            for issue in set(critical_issues):  # Remove duplicates
                print(f"  • {issue}")
        else:
            print("\n✅ NO CRITICAL ISSUES FOUND")
        
        if failed_tests > 0:
            print("\n📋 DETAILED FAILURE ANALYSIS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)
        
        # Save detailed results to file
        with open('/app/events_cash_bug_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"📄 Detailed results saved to: /app/events_cash_bug_test_results.json")

def main():
    """Main test execution"""
    tester = EventsCashBugTester()
    
    try:
        success = tester.run_critical_bug_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())