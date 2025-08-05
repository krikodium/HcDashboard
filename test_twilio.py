#!/usr/bin/env python3
"""
Simple test to verify Twilio integration and send a test notification
"""

import sys
import os
import asyncio
sys.path.append("/app/backend")

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

# Set environment to ensure proper imports
os.environ["PYTHONPATH"] = "/app/backend"

try:
    from services.notification_service import notification_service, DEFAULT_ADMIN_PREFERENCES
    
    print("🔍 Testing Twilio Integration...")
    
    # Check if Twilio client is initialized
    if notification_service.twilio_client:
        print("✅ Twilio client is initialized (LIVE MODE)")
        # Get account SID from environment since client.api.account_sid doesn't work the same way
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        print(f"   Account SID: {account_sid[:10]}...{account_sid[-4:] if account_sid else 'unknown'}")
    else:
        print("⚠️ Twilio client not initialized (MOCK MODE)")
        print("   Checking credentials...")
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        print(f"   Account SID present: {'Yes' if account_sid else 'No'}")
        print(f"   Auth Token present: {'Yes' if auth_token else 'No'}")
        if account_sid:
            print(f"   Account SID starts with: {account_sid[:10]}...")
    
    # Try to send a test WhatsApp notification
    print("\n📱 Sending test WhatsApp notification...")
    
    async def test_whatsapp():
        result = await notification_service.send_whatsapp(
            to="+5491112345678",  # Test number
            message="🎉 Test notification from Hermanas Caradonti Admin Tool!\n\nThis is a test of the notification system integration.",
        )
        return result
    
    whatsapp_result = asyncio.run(test_whatsapp())
    
    if whatsapp_result and whatsapp_result.get("success"):
        print("✅ Test WhatsApp notification sent successfully")
        print(f"   Status: {whatsapp_result.get('status', 'unknown')}")
        if "message_id" in whatsapp_result:
            print(f"   Message ID: {whatsapp_result['message_id']}")
    else:
        print("❌ Test WhatsApp notification failed")
        if whatsapp_result:
            print(f"   Error: {whatsapp_result.get('error', 'unknown')}")
    
    # Test the full notification service
    print("\n📧 Testing full notification service...")
    
    async def test_full_notification():
        result = await notification_service.send_notification(
            user_preferences=DEFAULT_ADMIN_PREFERENCES,
            notification_type="system_test",
            title="System Test",
            message="This is a comprehensive test of the notification system.\n\nAll modules are working correctly!",
            data={"test": True, "timestamp": "2024-01-01T12:00:00"}
        )
        return result
    
    # Run the async test
    full_result = asyncio.run(test_full_notification())
    
    if full_result and full_result.get("success"):
        print("✅ Full notification service test passed")
        print(f"   WhatsApp: {full_result.get('whatsapp', {}).get('success', False)}")
        print(f"   Email: {full_result.get('email', {}).get('success', False)}")
    else:
        print("❌ Full notification service test failed")
        if full_result:
            print(f"   Error: {full_result.get('error', 'unknown')}")
    
    print("\n🎊 Notification system verification complete!")
    
except Exception as e:
    print(f"❌ Error testing notification system: {e}")
    import traceback
    traceback.print_exc()