#!/usr/bin/env python3
"""
Simple test to verify Twilio integration and send a test notification
"""

import sys
import os
sys.path.append("/app/backend")

# Set environment to ensure proper imports
os.environ["PYTHONPATH"] = "/app/backend"

try:
    from services.notification_service import notification_service, DEFAULT_ADMIN_PREFERENCES
    
    print("🔍 Testing Twilio Integration...")
    
    # Check if Twilio client is initialized
    if notification_service.twilio_client:
        print("✅ Twilio client is initialized (LIVE MODE)")
        print(f"   Account SID: {notification_service.twilio_client.api.account_sid}")
    else:
        print("⚠️ Twilio client not initialized (MOCK MODE)")
    
    # Try to send a test notification
    print("\n📱 Sending test WhatsApp notification...")
    
    test_result = notification_service.send_whatsapp_notification(
        to_number="+5491112345678",  # Test number
        message="🎉 Test notification from Hermanas Caradonti Admin Tool!\n\nThis is a test of the notification system integration."
    )
    
    if test_result:
        print("✅ Test WhatsApp notification sent successfully")
    else:
        print("❌ Test WhatsApp notification failed")
    
    # Test the full notification service
    print("\n📧 Testing full notification service...")
    import asyncio
    
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
    
    if full_result:
        print("✅ Full notification service test passed")
    else:
        print("❌ Full notification service test failed")
    
    print("\n🎊 Notification system verification complete!")
    
except Exception as e:
    print(f"❌ Error testing notification system: {e}")
    import traceback
    traceback.print_exc()