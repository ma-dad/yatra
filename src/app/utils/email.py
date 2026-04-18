import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def send_email(
    to_emails: List[str],
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """Send email notification.

    When ``settings.EMAIL_LOG_ONLY`` is *True* (the default) the message is
    written to the application log instead of being delivered via SMTP.  Set
    ``EMAIL_LOG_ONLY=false`` in the environment together with the SMTP_* vars
    to enable real delivery.
    """

    # --- Log-only mode (default for dev / testing) --------------------------
    if settings.EMAIL_LOG_ONLY:
        logger.info(
            "[EMAIL LOG-ONLY] To: %s | Subject: %s\n%s",
            ", ".join(to_emails),
            subject,
            body,
        )
        return True

    # --- Real SMTP delivery --------------------------------------------------
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning("Email not configured, skipping notification")
        return False

    smtp_port = settings.SMTP_PORT if settings.SMTP_PORT is not None else 587

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.SMTP_USER
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject

        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)

        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

        with smtplib.SMTP(settings.SMTP_HOST, smtp_port) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {to_emails}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


def send_match_notification(seeker_email: str, volunteer_email: str, match_details: dict):
    """Send notification when a match is found"""
    
    subject = "New Travel Assistance Match Found - Yatra"
    
    seeker_body = f"""
    Hello!
    
    Great news! We found a volunteer who can assist you during your travel.
    
    Travel Details:
    - Flight: {match_details.get('flight_number', 'N/A')}
    - Route: {match_details.get('source', 'N/A')} → {match_details.get('destination', 'N/A')}
    - Date: {match_details.get('travel_time', 'N/A')}
    
    Log in to the Yatra platform to view full details and connect with your volunteer.
    
    Best regards,
    Yatra Team
    """
    
    volunteer_body = f"""
    Hello!
    
    A traveler needs your assistance on a route you're traveling.
    
    Travel Details:
    - Flight: {match_details.get('flight_number', 'N/A')}
    - Route: {match_details.get('source', 'N/A')} → {match_details.get('destination', 'N/A')}
    - Date: {match_details.get('travel_time', 'N/A')}
    
    Log in to the Yatra platform to review the request and decide if you can help.
    
    Best regards,
    Yatra Team
    """
    
    # Send to both parties
    send_email([seeker_email], subject, seeker_body)
    send_email([volunteer_email], subject, volunteer_body)


def send_contact_exchange_notification(
    to_email: str, 
    contact_name: str, 
    contact_email: str,
    contact_phone: Optional[str] = None
):
    """Send notification with contact details after match acceptance"""
    
    subject = "Contact Information Shared - Yatra"
    
    body = f"""
    Hello!
    
    Your match has been accepted! Here are the contact details:
    
    Name: {contact_name}
    Email: {contact_email}
    {f'Phone: {contact_phone}' if contact_phone else ''}
    
    Please coordinate with each other for meeting points and assistance details.
    
    Best regards,
    Yatra Team
    """
    
    send_email([to_email], subject, body)
