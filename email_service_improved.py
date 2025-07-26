import smtplib
import requests
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
from datetime import datetime
import streamlit as st
from typing import Tuple, List, Dict

class EnhancedEmailService:
    def __init__(self):
        self.providers = [
            self.send_via_sendgrid,
            self.send_via_resend,
            self.send_via_mailgun,
            self.send_via_gmail,
            self.send_via_outlook
        ]
        self.delivery_status = []
    
    def send_via_sendgrid(self, recipient: str, subject: str, content: str) -> Tuple[bool, str]:
        """SendGrid API - Most reliable"""
        api_key = os.getenv('SENDGRID_API_KEY')
        if not api_key:
            return False, "SendGrid not configured"
        
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "personalizations": [{"to": [{"email": recipient}]}],
            "from": {"email": "noreply@college.edu", "name": "College Chatbot"},
            "subject": subject,
            "content": [{"type": "text/plain", "value": content}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 202:
                return True, "Email sent via SendGrid"
            return False, f"SendGrid error: {response.status_code}"
        except Exception as e:
            return False, f"SendGrid failed: {str(e)}"
    
    def send_via_resend(self, recipient: str, subject: str, content: str) -> Tuple[bool, str]:
        """Resend API - Modern alternative"""
        api_key = os.getenv('RESEND_API_KEY')
        if not api_key:
            return False, "Resend not configured"
        
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "from": "College Chatbot <noreply@college.edu>",
            "to": [recipient],
            "subject": subject,
            "text": content
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                return True, "Email sent via Resend"
            return False, f"Resend error: {response.status_code}"
        except Exception as e:
            return False, f"Resend failed: {str(e)}"
    
    def send_email_with_tracking(self, recipient: str, conversation_history: List[Dict]) -> Tuple[bool, str]:
        """Send email with delivery tracking"""
        
        # Format content
        subject = "College Admission Chat Summary"
        content = self._format_email_content(conversation_history)
        
        # Try each provider
        for i, provider in enumerate(self.providers, 1):
            st.sidebar.info(f"🔄 Trying provider {i}/{len(self.providers)}...")
            
            try:
                success, message = provider(recipient, subject, content)
                
                # Log attempt
                self.delivery_status.append({
                    'provider': provider.__name__,
                    'success': success,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                })
                
                if success:
                    st.sidebar.success(f"✅ {message}")
                    self._save_delivery_log(recipient, success, message)
                    return True, message
                else:
                    st.sidebar.warning(f"⚠️ {message}")
                    
            except Exception as e:
                error_msg = f"Provider {provider.__name__} failed: {str(e)}"
                st.sidebar.error(f"❌ {error_msg}")
                self.delivery_status.append({
                    'provider': provider.__name__,
                    'success': False,
                    'message': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
        
        # All providers failed
        self._save_failed_email(recipient, conversation_history)
        return False, "All email providers failed. Email queued for manual delivery."
    
    def _format_email_content(self, conversation_history: List[Dict]) -> str:
        """Format conversation for email"""
        content = f"""
Dear Student,

Thank you for using our College Admission Chatbot. Here's your conversation summary:

{'='*60}
COLLEGE ADMISSION CHAT SUMMARY
{'='*60}

"""
        
        for i, qa in enumerate(conversation_history, 1):
            content += f"""
📝 Question {i}: {qa['question']}
💬 Answer: {qa['answer']}
{'─'*50}
"""
        
        content += f"""

📞 Need more help? Contact us:
📧 Email: admissions@college.edu
📱 Phone: +91-1234567890
🌐 Website: www.college.edu

🎓 Best regards,
College Admission Team

---
This email was generated automatically from your chat session.
Chat ID: {datetime.now().strftime('%Y%m%d_%H%M%S')}
"""
        return content
    
    def _save_delivery_log(self, recipient: str, success: bool, message: str):
        """Save delivery log"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'recipient': recipient,
            'success': success,
            'message': message,
            'delivery_attempts': len(self.delivery_status)
        }
        
        try:
            # Load existing logs
            try:
                with open('email_delivery_log.json', 'r') as f:
                    logs = json.load(f)
            except FileNotFoundError:
                logs = []
            
            logs.append(log_entry)
            
            # Keep only last 1000 logs
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open('email_delivery_log.json', 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            st.sidebar.warning(f"Could not save delivery log: {e}")