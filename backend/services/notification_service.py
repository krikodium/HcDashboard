import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from twilio.rest import Client
import sendgrid
from sendgrid.helpers.mail import Mail
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    """
    Unified notification service supporting WhatsApp (Twilio) and Email (SendGrid/SMTP)
    Uses mock services in development and real services in production
    """
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.twilio_client = None
        self.sendgrid_client = None
        
        # Initialize services
        self._init_twilio()
        self._init_sendgrid()
    
    def _init_twilio(self):
        """Initialize Twilio client for WhatsApp"""
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        
        if account_sid and auth_token and account_sid != "your_twilio_account_sid_here":
            try:
                self.twilio_client = Client(account_sid, auth_token)
                logger.info("✅ Twilio client initialized")
            except Exception as e:
                logger.error(f"❌ Twilio initialization failed: {e}")
        else:
            logger.info("📱 Twilio running in MOCK mode - messages will be logged")
    
    def _init_sendgrid(self):
        """Initialize SendGrid client for email"""
        api_key = os.getenv("SENDGRID_API_KEY")
        
        if api_key and api_key != "your_sendgrid_api_key_here":
            try:
                self.sendgrid_client = sendgrid.SendGridAPIClient(api_key=api_key)
                logger.info("✅ SendGrid client initialized")
            except Exception as e:
                logger.error(f"❌ SendGrid initialization failed: {e}")
        else:
            logger.info("📧 Email running in MOCK mode - messages will be logged")
    
    async def send_whatsapp(self, to: str, message: str, template_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send WhatsApp message via Twilio
        """
        try:
            if self.twilio_client:
                # Production WhatsApp sending
                whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
                to_whatsapp = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
                
                message_instance = self.twilio_client.messages.create(
                    body=message,
                    from_=whatsapp_from,
                    to=to_whatsapp
                )
                
                logger.info(f"✅ WhatsApp sent to {to}: {message_instance.sid}")
                return {
                    "success": True,
                    "message_id": message_instance.sid,
                    "status": message_instance.status
                }
            else:
                # Mock mode - log the message
                logger.info(f"📱 MOCK WhatsApp to {to}: {message}")
                return {
                    "success": True,
                    "message_id": f"mock_wa_{datetime.now().timestamp()}",
                    "status": "mock_sent"
                }
                
        except Exception as e:
            logger.error(f"❌ WhatsApp send failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_email(self, to: str, subject: str, content: str, template_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send email via SendGrid or SMTP fallback
        """
        try:
            from_email = os.getenv("EMAIL_FROM", "admin@hermanascaradonti.com")
            from_name = os.getenv("EMAIL_FROM_NAME", "Hermanas Caradonti Admin")
            
            if self.sendgrid_client:
                # SendGrid sending
                mail = Mail(
                    from_email=(from_email, from_name),
                    to_emails=to,
                    subject=subject,
                    html_content=content
                )
                
                response = self.sendgrid_client.send(mail)
                logger.info(f"✅ Email sent via SendGrid to {to}: {response.status_code}")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "method": "sendgrid"
                }
            else:
                # Mock mode - log the email
                logger.info(f"📧 MOCK Email to {to}")
                logger.info(f"   Subject: {subject}")
                logger.info(f"   Content: {content[:100]}...")
                return {
                    "success": True,
                    "message_id": f"mock_email_{datetime.now().timestamp()}",
                    "method": "mock"
                }
                
        except Exception as e:
            logger.error(f"❌ Email send failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_notification(self, 
                              user_preferences: Dict[str, Any],
                              notification_type: str,
                              title: str,
                              message: str,
                              data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send notification based on user preferences
        user_preferences format: {
            "whatsapp": {"enabled": bool, "number": str},
            "email": {"enabled": bool, "address": str}
        }
        """
        results = []
        
        # Send WhatsApp if enabled
        if user_preferences.get("whatsapp", {}).get("enabled", False):
            whatsapp_number = user_preferences["whatsapp"]["number"]
            whatsapp_message = f"*{title}*\n\n{message}"
            
            if data:
                whatsapp_message += f"\n\nDetails: {data}"
            
            whatsapp_result = await self.send_whatsapp(whatsapp_number, whatsapp_message)
            results.append({"channel": "whatsapp", "result": whatsapp_result})
        
        # Send Email if enabled
        if user_preferences.get("email", {}).get("enabled", False):
            email_address = user_preferences["email"]["address"]
            email_content = f"""
            <html>
                <body>
                    <h2>{title}</h2>
                    <p>{message}</p>
                    {f'<pre>{data}</pre>' if data else ''}
                    <hr>
                    <p><small>Hermanas Caradonti Admin Tool</small></p>
                </body>
            </html>
            """
            
            email_result = await self.send_email(email_address, title, email_content)
            results.append({"channel": "email", "result": email_result})
        
        return {
            "notification_type": notification_type,
            "sent_at": datetime.utcnow().isoformat(),
            "results": results
        }

# Global notification service instance
notification_service = NotificationService()

# Convenience functions for common notification types
async def notify_payment_approval_needed(user_prefs: Dict, amount: float, currency: str, description: str):
    """Notify when payment approval is needed"""
    return await notification_service.send_notification(
        user_preferences=user_prefs,
        notification_type="payment_approval",
        title="Payment Approval Required",
        message=f"A payment of {currency} {amount:,.2f} requires approval.\n\nDescription: {description}",
        data={"amount": amount, "currency": currency, "description": description}
    )

async def notify_payment_approved(user_prefs: Dict, amount: float, currency: str, approved_by: str):
    """Notify when payment is approved"""
    return await notification_service.send_notification(
        user_preferences=user_prefs,
        notification_type="payment_approved",
        title="Payment Approved",
        message=f"Payment of {currency} {amount:,.2f} has been approved by {approved_by}.",
        data={"amount": amount, "currency": currency, "approved_by": approved_by}
    )

async def notify_low_stock(user_prefs: Dict, item_name: str, current_stock: int, threshold: int):
    """Notify when inventory is low"""
    return await notification_service.send_notification(
        user_preferences=user_prefs,
        notification_type="low_stock",
        title="Low Stock Alert",
        message=f"Item '{item_name}' is running low.\n\nCurrent stock: {current_stock}\nThreshold: {threshold}",
        data={"item": item_name, "stock": current_stock, "threshold": threshold}
    )

async def notify_reconciliation_discrepancy(user_prefs: Dict, deco_name: str, discrepancy: float, currency: str):
    """Notify when cash count discrepancy is found"""
    return await notification_service.send_notification(
        user_preferences=user_prefs,
        notification_type="reconciliation_discrepancy",
        title="Cash Count Discrepancy",
        message=f"Discrepancy found in {deco_name} cash count.\n\nAmount: {currency} {discrepancy:,.2f}",
        data={"deco": deco_name, "discrepancy": discrepancy, "currency": currency}
    )