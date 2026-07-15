"""
Send conversation transcripts via email.

Uses SMTP to send plaintext email with conversation history.
Requires SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD in .env
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def send_transcript_email(to_email: str, transcript: str, document_name: str) -> None:
    """
    Send a conversation transcript via SMTP email.

    Args:
        to_email: Recipient email address
        transcript: Plain-text conversation transcript
        document_name: Name of the document discussed (for subject line)

    Raises:
        RuntimeError: If email sending fails (SMTP error, missing credentials, etc.)
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    # Validate required credentials
    if not all([smtp_host, smtp_port, smtp_user, smtp_password]):
        raise RuntimeError(
            "Email configuration incomplete. Please set in .env:\n"
            "  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD\n"
            "Example for Gmail:\n"
            "  SMTP_HOST=smtp.gmail.com\n"
            "  SMTP_PORT=587\n"
            "  SMTP_USER=your-email@gmail.com\n"
            "  SMTP_PASSWORD=your-app-password (not your account password)"
        )

    try:
        smtp_port = int(smtp_port)
    except ValueError:
        raise RuntimeError(f"SMTP_PORT must be a number, got: {smtp_port}")

    # Build email
    subject = f"Conversation transcript: {document_name} ({datetime.now().strftime('%Y-%m-%d')})"

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject

    body = f"""Conversation Transcript
======================

Document: {document_name}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{transcript}

---
Sent by Voice Document Agent
"""

    msg.attach(MIMEText(body, "plain"))

    # Send email
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        raise RuntimeError(
            "SMTP login failed. Check your credentials in .env:\n"
            "  - For Gmail: use an app password, not your account password\n"
            "  - Verify SMTP_USER and SMTP_PASSWORD are correct"
        )
    except smtplib.SMTPException as e:
        raise RuntimeError(f"SMTP error: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}")
