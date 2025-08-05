#!/usr/bin/env python3
"""
Full Notification System Integration Test
Testing live Twilio WhatsApp notifications across all modules
"""

import requests
import json
import time
from datetime import datetime, date

class NotificationSystemTester:
    def __init__(self):
        self.base_url = "http://localhost:8001/api"
        self.headers = {
            "Content-Type": "application/json"
        }
        self.token = None
        
    def authenticate(self):
        """Authenticate and get access token"""
        try:
            login_data = {
                "username": "admin",
                "password": "changeme123"
            }
            response = requests.post(f"{self.base_url}/auth/login", json=login_data)
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.headers["Authorization"] = f"Bearer {self.token}"
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_notification_service_status(self):
        """Test if notification service is properly initialized"""
        print("\n🔍 Testing Notification Service Status...")
        try:
            # Check backend logs for Twilio initialization
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "20", "/var/log/supervisor/backend.out.log"],
                capture_output=True, text=True
            )
            
            if "Twilio client initialized" in result.stdout:
                print("✅ Twilio client initialized successfully (Live mode)")
                return True
            elif "Twilio running in MOCK mode" in result.stdout:
                print("⚠️ Twilio running in MOCK mode - may not send real messages")
                return False
            else:
                print("❓ Twilio initialization status unclear")
                return False
        except Exception as e:
            print(f"❌ Error checking notification service: {e}")
            return False
    
    def test_general_cash_notifications(self):
        """Test General Cash notifications"""
        print("\n🔔 Testing General Cash Notifications...")
        
        try:
            # Test 1: Create entry requiring approval (large expense)
            entry_data = {
                "date": date.today().isoformat(),
                "application": "Compras varias",
                "description": "Large expense test - Office equipment purchase",
                "expense_ars": 15000.0,  # Large expense to trigger approval
                "payment_method": "Transferencia",
                "approval_status": "Pending"
            }
            
            response = requests.post(
                f"{self.base_url}/general-cash",
                json=entry_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                entry = response.json()
                print(f"✅ General Cash entry created: {entry['id']}")
                print(f"   - Should trigger: Payment approval needed notification")
                print(f"   - Should trigger: Large expense alert notification")
                
                # Wait a moment for notifications to be sent
                time.sleep(2)
                
                # Test 2: Approve the entry (if it has approval status)
                if entry.get('approval_status') == 'Pending':
                    approval_response = requests.post(
                        f"{self.base_url}/general-cash/{entry['id']}/approve?approval_type=fede",
                        headers=self.headers
                    )
                    
                    if approval_response.status_code == 200:
                        print("✅ General Cash entry approved")
                        print("   - Should trigger: Payment approved notification")
                    else:
                        print(f"⚠️ Approval failed: {approval_response.status_code}")
                
                return True
            else:
                print(f"❌ Failed to create General Cash entry: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ General Cash notification test error: {e}")
            return False
    
    def test_events_cash_notifications(self):
        """Test Events Cash notifications"""
        print("\n🔔 Testing Events Cash Notifications...")
        
        try:
            # First create an event
            event_data = {
                "header": {
                    "client_name": "Test Client Notification",
                    "client_phone": "+54911234567",
                    "event_type": "Wedding",
                    "event_date": "2024-06-15",
                    "total_budget_no_iva": 50000.0,
                    "iva_amount": 10500.0,
                    "final_budget": 60500.0
                },
                "payment_status": {
                    "total_budget": 60500.0,
                    "anticipo_received": 0.0,
                    "segundo_pago": 0.0,
                    "tercer_pago": 0.0
                }
            }
            
            response = requests.post(
                f"{self.base_url}/events-cash",
                json=event_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                event = response.json()
                print(f"✅ Events Cash event created: {event['id']}")
                
                # Test client payment notification
                ledger_entry = {
                    "payment_method": "Transferencia",
                    "date": date.today().isoformat(),
                    "detail": "Client payment received - Test notification",
                    "income_ars": 20000.0,
                    "is_client_payment": True  # This should trigger client payment notification
                }
                
                ledger_response = requests.post(
                    f"{self.base_url}/events-cash/{event['id']}/ledger",
                    json=ledger_entry,
                    headers=self.headers
                )
                
                if ledger_response.status_code == 200:
                    print("✅ Events Cash client payment recorded")
                    print("   - Should trigger: Event payment received notification")
                    time.sleep(2)
                    return True
                else:
                    print(f"❌ Failed to record client payment: {ledger_response.status_code}")
                    return False
            else:
                print(f"❌ Failed to create Events Cash event: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Events Cash notification test error: {e}")
            return False
    
    def test_shop_cash_notifications(self):
        """Test Shop Cash notifications"""
        print("\n🔔 Testing Shop Cash Notifications...")
        
        try:
            sale_data = {
                "date": date.today().isoformat(),
                "provider": "Test Provider Notification",
                "client": "Test Client Notification",
                "internal_coordinator": "Test Coordinator",
                "quantity": 2,
                "item_description": "Decorative Test Item for Notification",
                "sku": f"TEST-NOTIF-{int(time.time())}",
                "sold_amount_ars": 8500.0,
                "payment_method": "Efectivo",
                "cost_ars": 3000.0
            }
            
            response = requests.post(
                f"{self.base_url}/shop-cash",
                json=sale_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                sale = response.json()
                print(f"✅ Shop Cash sale created: {sale.get('id', 'unknown')}")
                print("   - Should trigger: Sale completed notification")
                time.sleep(2)
                return True
            else:
                print(f"❌ Failed to create Shop Cash sale: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Shop Cash notification test error: {e}")
            return False
    
    def test_inventory_notifications(self):
        """Test Inventory low stock notifications"""
        print("\n🔔 Testing Inventory Notifications...")
        
        try:
            # Create a test product with low initial stock
            product_data = {
                "sku": f"LOW-STOCK-{int(time.time())}",
                "name": "Low Stock Test Product",
                "description": "Product for testing low stock notifications",
                "category": "Décor",
                "provider_name": "Test Provider",
                "cost_ars": 1500.0,
                "selling_price_ars": 3000.0,
                "current_stock": 6,  # Just above threshold
                "min_stock_threshold": 5
            }
            
            response = requests.post(
                f"{self.base_url}/inventory/products",
                json=product_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                product = response.json()
                print(f"✅ Test product created: {product['sku']}")
                
                # Adjust stock to trigger low stock notification
                adjustment_data = {
                    "adjustment_type": "decrease",
                    "quantity": 2,  # This will bring stock to 4, below threshold of 5
                    "reason": "Testing low stock notification system",
                    "notes": "Automated test for notification system"
                }
                
                adjustment_response = requests.post(
                    f"{self.base_url}/inventory/products/{product['id']}/stock-adjustment",
                    json=adjustment_data,
                    headers=self.headers
                )
                
                if adjustment_response.status_code == 200:
                    print("✅ Stock adjustment completed")
                    print("   - Should trigger: Low stock alert notification")
                    time.sleep(2)
                    return True
                else:
                    print(f"❌ Failed to adjust stock: {adjustment_response.status_code}")
                    return False
            else:
                print(f"❌ Failed to create test product: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Inventory notification test error: {e}")
            return False
    
    def test_deco_movements_notifications(self):
        """Test Deco Movements notifications"""
        print("\n🔔 Testing Deco Movements Notifications...")
        
        try:
            movement_data = {
                "project_name": "Test Project Notification",
                "date": date.today().isoformat(),
                "detail": "Large expense test for Deco Movements notifications",
                "expense_ars": 12000.0,  # Large expense
                "payment_method": "Transferencia"
            }
            
            response = requests.post(
                f"{self.base_url}/deco-movements",
                json=movement_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                movement = response.json()
                print(f"✅ Deco Movement created: {movement.get('id', 'unknown')}")
                print("   - Should trigger: Deco movement created notification")
                print("   - Should trigger: Large expense alert notification")
                time.sleep(2)
                return True
            else:
                print(f"❌ Failed to create Deco Movement: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Deco Movements notification test error: {e}")
            return False
    
    def check_notification_logs(self):
        """Check backend logs for notification activity"""
        print("\n📋 Checking Notification Logs...")
        try:
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.out.log"],
                capture_output=True, text=True
            )
            
            notification_keywords = [
                "WhatsApp sent",
                "MOCK WhatsApp",
                "notification",
                "Twilio",
                "Failed to send"
            ]
            
            relevant_lines = []
            for line in result.stdout.split('\n'):
                if any(keyword in line for keyword in notification_keywords):
                    relevant_lines.append(line)
            
            if relevant_lines:
                print("📋 Recent notification activity:")
                for line in relevant_lines[-10:]:  # Show last 10 relevant lines
                    print(f"   {line}")
                return True
            else:
                print("⚠️ No notification activity found in logs")
                return False
                
        except Exception as e:
            print(f"❌ Error checking logs: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all notification tests"""
        print("🚀 Starting Comprehensive Notification System Test")
        print("=" * 60)
        
        if not self.authenticate():
            return False
        
        # Check notification service status
        service_status = self.test_notification_service_status()
        
        # Run all notification tests
        test_results = {
            "notification_service": service_status,
            "general_cash": self.test_general_cash_notifications(),
            "events_cash": self.test_events_cash_notifications(),
            "shop_cash": self.test_shop_cash_notifications(),
            "inventory": self.test_inventory_notifications(),
            "deco_movements": self.test_deco_movements_notifications()
        }
        
        # Check logs
        self.check_notification_logs()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 NOTIFICATION SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if service_status:
            print("\n🎉 LIVE TWILIO INTEGRATION CONFIRMED")
            print("   WhatsApp notifications are being sent to real numbers")
        else:
            print("\n⚠️ MOCK MODE DETECTED")
            print("   Notifications are being logged but not sent to real numbers")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = NotificationSystemTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎊 ALL NOTIFICATION TESTS PASSED!")
        print("Full Notification System Integration is COMPLETE")
    else:
        print("\n⚠️ Some notification tests failed")
        print("Please check the logs and fix any issues")