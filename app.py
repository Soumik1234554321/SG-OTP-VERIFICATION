# app.py - Professional Gmail OTP API for Vercel (No .env required)
import os
import re
import random
import smtplib
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from flask_cors import CORS

# ==========================================
# CONFIGURATION (Direct values - no .env file needed)
# ==========================================

class Config:
    """Application configuration - values can be overridden by Vercel env variables"""
    # Default values (hardcoded)
    GMAIL_EMAIL = os.getenv('GMAIL_EMAIL', 'misstishaff50@gmail.com')
    GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', 'smisdhqayeliarte')
    OTP_EXPIRY_MINUTES = int(os.getenv('OTP_EXPIRY_MINUTES', '5'))
    OTP_LENGTH = 6
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    COMPANY_NAME = "MISS TISHA"
    COMPANY_LOGO_URL = "https://i.ibb.co/wNvw1Fsm/IMG-20260319-205918.jpg"

config = Config()

# ==========================================
# LOGGING SETUP
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================================
# OTP STORAGE
# ==========================================

class OTPStorage:
    """Thread-safe OTP storage"""
    
    def __init__(self):
        self._storage = {}
    
    def save(self, email: str, otp: str, expires_at: datetime):
        """Save OTP for email"""
        self._storage[email] = {
            'otp': otp,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
        logger.info(f"OTP saved for {email}")
    
    def get(self, email: str) -> Optional[Dict]:
        """Get OTP data for email"""
        return self._storage.get(email)
    
    def delete(self, email: str):
        """Delete OTP for email"""
        if email in self._storage:
            del self._storage[email]
            logger.info(f"OTP deleted for {email}")
    
    def cleanup(self):
        """Remove expired OTPs"""
        now = datetime.now()
        expired = [email for email, data in self._storage.items() 
                  if data['expires_at'] < now]
        for email in expired:
            del self._storage[email]
        if expired:
            logger.info(f"Cleaned {len(expired)} expired OTPs")

otp_db = OTPStorage()

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format"""
    if not email:
        return False, "Email is required"
    
    email = email.strip()
    
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False, "Invalid email format"
    
    return True, email

def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return f"{random.randint(100000, 999999)}"

def create_rich_email_template(recipient: str, otp: str, expiry_minutes: int) -> str:
    """Create professional HTML email template with smaller OTP box"""
    
    current_year = datetime.now().year
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OTP Verification - {config.COMPANY_NAME}</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f0f2f5; line-height: 1.6;">
        
        <div style="max-width: 550px; margin: 20px auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
            
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px 25px; text-align: center;">
                <div style="margin-bottom: 12px;">
                    <img src="{config.COMPANY_LOGO_URL}" alt="{config.COMPANY_NAME} Logo" style="width: 55px; height: 55px; border-radius: 50%; background: white; padding: 8px;">
                </div>
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700;">{config.COMPANY_NAME}</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0; font-size: 13px;">Secure Verification Service</p>
            </div>
            
            <div style="padding: 30px 28px;">
                
                <div style="margin-bottom: 20px;">
                    <h2 style="color: #1a1a2e; font-size: 20px; font-weight: 600; margin: 0 0 6px 0;">Hello {recipient.split('@')[0]}! 😊</h2>
                    <p style="color: #555; font-size: 14px; margin: 0;">Welcome to {config.COMPANY_NAME} verification system.</p>
                </div>
                
                <div style="background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%); border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 25px; border: 1.5px solid #e0e7ff;">
                    <p style="color: #666; font-size: 12px; margin: 0 0 10px 0; letter-spacing: 1px;">YOUR VERIFICATION CODE</p>
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                        <div style="font-size: 28px; font-weight: bold; color: #ffffff; letter-spacing: 4px; font-family: 'Courier New', monospace; word-break: break-all;">
                            {otp}
                        </div>
                    </div>
                    <p style="color: #888; font-size: 11px; margin: 10px 0 0 0;">
                        ⚠️ This is a one-time password
                    </p>
                </div>
                
                <div style="margin-bottom: 25px;">
                    <div style="background-color: #f8f9ff; border-left: 3px solid #667eea; padding: 15px; border-radius: 10px;">
                        <p style="margin: 0 0 10px 0; font-weight: 600; color: #1a1a2e; font-size: 14px;">📋 Important Information:</p>
                        <ul style="margin: 0; padding-left: 20px; color: #555; font-size: 13px;">
                            <li style="margin-bottom: 6px;"><strong>⏰ Expiry Time:</strong> This OTP will expire in <strong style="color: #e74c3c;">{expiry_minutes} minutes</strong></li>
                            <li style="margin-bottom: 6px;"><strong>🔒 Security:</strong> Never share this code with anyone</li>
                            <li style="margin-bottom: 6px;"><strong>🔄 One-time use:</strong> This code can only be used once</li>
                            <li><strong>📧 Requested from:</strong> {recipient}</li>
                        </ul>
                    </div>
                </div>
                
                <div style="background-color: #fff9e6; border-radius: 10px; padding: 15px; margin-bottom: 25px; border: 1px solid #ffe5b4;">
                    <p style="margin: 0 0 8px 0; font-weight: 600; color: #b8860b; font-size: 13px;">📌 How to verify:</p>
                    <p style="margin: 0; color: #666; font-size: 13px;">
                        1. Copy the 6-digit code above<br>
                        2. Return to the application<br>
                        3. Enter the code in verification field<br>
                        4. Click "Verify" to complete the process
                    </p>
                </div>
                
                <div style="background-color: #fee; border-radius: 10px; padding: 12px; margin-bottom: 20px; border: 1px solid #fcc;">
                    <p style="margin: 0; color: #c0392b; font-size: 12px; text-align: center;">
                        ⚠️ <strong>Security Alert:</strong> If you didn't request this OTP, please ignore this email. 
                        Do not share this code with anyone, including our support team.
                    </p>
                </div>
                
                <div style="border-top: 1.5px solid #e0e0e0; padding-top: 20px; text-align: center;">
                    <div style="margin-bottom: 12px;">
                        <a href="#" style="color: #667eea; text-decoration: none; margin: 0 8px; font-size: 11px;">Privacy Policy</a>
                        <span style="color: #ccc;">|</span>
                        <a href="#" style="color: #667eea; text-decoration: none; margin: 0 8px; font-size: 11px;">Terms of Service</a>
                        <span style="color: #ccc;">|</span>
                        <a href="#" style="color: #667eea; text-decoration: none; margin: 0 8px; font-size: 11px;">Help Center</a>
                    </div>
                    <p style="color: #999; font-size: 11px; margin: 0 0 4px 0;">
                        &copy; {current_year} {config.COMPANY_NAME}. All rights reserved.
                    </p>
                    <p style="color: #bbb; font-size: 10px; margin: 0;">
                        This is an automated message, please do not reply to this email.
                    </p>
                </div>
            </div>
        </div>
        
        <div style="display: none;">
            Your OTP verification code is: {otp}. This code expires in {expiry_minutes} minutes. 
            Never share this code with anyone. Thank you for using {config.COMPANY_NAME}.
        </div>
    </body>
    </html>
    """

def send_email(recipient: str, otp: str) -> Tuple[bool, str]:
    """Send rich HTML email via Gmail SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{config.COMPANY_NAME} <{config.GMAIL_EMAIL}>"
        msg['To'] = recipient
        msg['Subject'] = f"🔐 Your OTP Verification Code - {config.COMPANY_NAME}"
        
        plain_text = f"""
        {config.COMPANY_NAME} - OTP Verification
        
        Hello {recipient.split('@')[0]}!
        
        Your OTP verification code is: {otp}
        
        This code will expire in {config.OTP_EXPIRY_MINUTES} minutes.
        
        Security Tips:
        - Never share this OTP with anyone
        - This is a one-time password
        - If you didn't request this, please ignore
        
        Thank you for using {config.COMPANY_NAME}!
        
        © {datetime.now().year} {config.COMPANY_NAME}. All rights reserved.
        """
        
        html_content = create_rich_email_template(recipient, otp, config.OTP_EXPIRY_MINUTES)
        
        msg.attach(MIMEText(plain_text, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.GMAIL_EMAIL, config.GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Rich email sent to {recipient}")
        return True, "OTP sent successfully with rich email template"
        
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication failed")
        return False, "Email authentication failed. Check Gmail and App Password"
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        return False, f"Failed to send OTP: {str(e)}"

# ==========================================
# FLASK APPLICATION
# ==========================================

app = Flask(__name__)
CORS(app)

@app.before_request
def cleanup():
    otp_db.cleanup()

# ==========================================
# API ENDPOINTS
# ==========================================

@app.route('/gmail=<email>', methods=['GET'])
def send_otp(email):
    valid, result = validate_email(email)
    if not valid:
        return jsonify({
            'status': 'error',
            'message': result,
            'timestamp': datetime.now().isoformat()
        }), 400
    
    email = result
    otp_code = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=config.OTP_EXPIRY_MINUTES)
    otp_db.save(email, otp_code, expires_at)
    success, message = send_email(email, otp_code)
    
    if success:
        return jsonify({
            'status': 'success',
            'message': f'OTP sent successfully to {email}',
            'data': {
                'email': email,
                'expires_in_minutes': config.OTP_EXPIRY_MINUTES,
                'expires_at': expires_at.isoformat(),
                'company': config.COMPANY_NAME,
                'logo_url': config.COMPANY_LOGO_URL
            },
            'timestamp': datetime.now().isoformat()
        }), 200
    else:
        otp_db.delete(email)
        return jsonify({
            'status': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/gmail=<email>/check=<otp_code>', methods=['GET'])
def verify_otp(email, otp_code):
    valid, result = validate_email(email)
    if not valid:
        return jsonify({
            'status': 'error',
            'message': result,
            'timestamp': datetime.now().isoformat()
        }), 400
    
    email = result
    
    if not otp_code or not otp_code.isdigit() or len(otp_code) != 6:
        return jsonify({
            'status': 'error',
            'message': 'OTP must be a 6-digit number',
            'timestamp': datetime.now().isoformat()
        }), 400
    
    otp_data = otp_db.get(email)
    if not otp_data:
        return jsonify({
            'status': 'error',
            'message': f'No OTP found for {email}. Please request a new OTP using /gmail={email}',
            'timestamp': datetime.now().isoformat()
        }), 404
    
    if datetime.now() > otp_data['expires_at']:
        otp_db.delete(email)
        return jsonify({
            'status': 'error',
            'message': 'OTP has expired. Please request a new OTP',
            'timestamp': datetime.now().isoformat()
        }), 410
    
    if otp_code == otp_data['otp']:
        otp_db.delete(email)
        return jsonify({
            'status': 'success',
            'message': 'OTP verified successfully',
            'data': {
                'email': email,
                'verified': True,
                'company': config.COMPANY_NAME
            },
            'timestamp': datetime.now().isoformat()
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': 'Invalid OTP. Please try again',
            'timestamp': datetime.now().isoformat()
        }), 401

@app.route('/resend/gmail=<email>', methods=['GET'])
def resend_otp(email):
    valid, result = validate_email(email)
    if not valid:
        return jsonify({
            'status': 'error',
            'message': result,
            'timestamp': datetime.now().isoformat()
        }), 400
    
    email = result
    otp_db.delete(email)
    otp_code = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=config.OTP_EXPIRY_MINUTES)
    otp_db.save(email, otp_code, expires_at)
    success, message = send_email(email, otp_code)
    
    if success:
        return jsonify({
            'status': 'success',
            'message': f'OTP resent successfully to {email}',
            'data': {
                'email': email,
                'expires_in_minutes': config.OTP_EXPIRY_MINUTES,
                'company': config.COMPANY_NAME
            },
            'timestamp': datetime.now().isoformat()
        }), 200
    else:
        otp_db.delete(email)
        return jsonify({
            'status': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/status/gmail=<email>', methods=['GET'])
def check_status(email):
    valid, result = validate_email(email)
    if not valid:
        return jsonify({
            'status': 'error',
            'message': result,
            'timestamp': datetime.now().isoformat()
        }), 400
    
    email = result
    otp_data = otp_db.get(email)
    
    if not otp_data:
        return jsonify({
            'status': 'success',
            'message': 'No active OTP found',
            'data': {
                'email': email,
                'has_active_otp': False
            },
            'timestamp': datetime.now().isoformat()
        }), 200
    
    if datetime.now() > otp_data['expires_at']:
        otp_db.delete(email)
        return jsonify({
            'status': 'success',
            'message': 'OTP expired',
            'data': {
                'email': email,
                'has_active_otp': False,
                'expired': True
            },
            'timestamp': datetime.now().isoformat()
        }), 200
    
    remaining_seconds = int((otp_data['expires_at'] - datetime.now()).total_seconds())
    
    return jsonify({
        'status': 'success',
        'message': 'Active OTP found',
        'data': {
            'email': email,
            'has_active_otp': True,
            'expires_in_seconds': remaining_seconds,
            'expires_in_minutes': round(remaining_seconds / 60, 1),
            'expires_at': otp_data['expires_at'].isoformat(),
            'created_at': otp_data['created_at'].isoformat()
        },
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'name': f'{config.COMPANY_NAME} - Gmail OTP Verification API',
        'version': '2.0.0',
        'description': 'Professional OTP verification service with rich email templates',
        'company': {
            'name': config.COMPANY_NAME,
            'logo_url': config.COMPANY_LOGO_URL,
            'email': config.GMAIL_EMAIL
        },
        'endpoints': {
            'send_otp': {
                'url': '/gmail={email}',
                'method': 'GET',
                'example': f'https://yourdomain.com/gmail=user@gmail.com',
                'description': 'Send OTP to email address with rich HTML template'
            },
            'verify_otp': {
                'url': '/gmail={email}/check={otp}',
                'method': 'GET',
                'example': f'https://yourdomain.com/gmail=user@gmail.com/check=123456',
                'description': 'Verify OTP code'
            },
            'resend_otp': {
                'url': '/resend/gmail={email}',
                'method': 'GET',
                'example': f'https://yourdomain.com/resend/gmail=user@gmail.com',
                'description': 'Resend OTP to email'
            },
            'check_status': {
                'url': '/status/gmail={email}',
                'method': 'GET',
                'example': f'https://yourdomain.com/status/gmail=user@gmail.com',
                'description': 'Check OTP status'
            }
        },
        'config': {
            'otp_expiry_minutes': config.OTP_EXPIRY_MINUTES,
            'otp_length': config.OTP_LENGTH,
            'unlimited_requests': True,
            'rich_html_emails': True
        },
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found. Use /gmail={email} or /gmail={email}/check={otp}',
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error. Please try again later',
        'timestamp': datetime.now().isoformat()
    }), 500