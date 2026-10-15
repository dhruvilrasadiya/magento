# email_config.py
import os
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class EmailConfig:
    """Configuration for email operations."""

    email: str
    password: str
    smtp_server: str
    smtp_port: int
    imap_server: str
    imap_port: int

    @classmethod
    def from_env(cls) -> "EmailConfig":
        """Create EmailConfig from environment variables."""
        email = os.getenv("SENDER_EMAIL")
        password = os.getenv("SENDER_PASSWORD")

        if not email or not password:
            raise ValueError(
                "SENDER_EMAIL and SENDER_PASSWORD must be set in environment variables"
            )

        return cls(
            email=email,
            password=password,
            smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            imap_server=os.getenv("IMAP_SERVER", "imap.gmail.com"),
            imap_port=int(os.getenv("IMAP_PORT", "993")),
        )

    @classmethod
    def gmail_config(cls, email: str, password: str) -> "EmailConfig":
        """Create Gmail configuration with App Password."""
        if not email or not password:
            raise ValueError("Email and App Password are required for Gmail")

        return cls(
            email=email,
            password=password,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            imap_server="imap.gmail.com",
            imap_port=993,
        )

    @classmethod
    def outlook_config(cls, email: str, password: str) -> "EmailConfig":
        """Create Outlook configuration."""
        if not email or not password:
            raise ValueError("Email and password are required for Outlook")

        return cls(
            email=email,
            password=password,
            smtp_server="smtp-mail.outlook.com",
            smtp_port=587,
            imap_server="outlook.office365.com",
            imap_port=993,
        )

    def test_smtp_connection(self) -> bool:
        """Test SMTP connection with the reliable method."""
        try:
            import smtplib

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            server.quit()
            return True
        except Exception as e:
            print(f"SMTP connection test failed: {e}")
            return False

    def test_imap_connection(self) -> bool:
        """Test IMAP connection with the reliable method."""
        try:
            import imaplib

            server = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            server.login(self.email, self.password)
            server.logout()
            return True
        except Exception as e:
            print(f"IMAP connection test failed: {e}")
            return False

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {
            "email": self.email,
            "password": self.password,
            "smtp_server": self.smtp_server,
            "smtp_port": self.smtp_port,
            "imap_server": self.imap_server,
            "imap_port": self.imap_port,
        }


# Usage example
def setup_email_config(email_provider: str = "gmail"):
    """Setup email configuration."""

    # Option 1: From environment variables
    email_config = EmailConfig.from_env()

    # Option 2: Provider-specific setup
    if email_provider == "gmail":
        email_config = EmailConfig.gmail_config(
            email="your_email@gmail.com",
            password="your_app_password",  # Use app password for Gmail
        )
    elif email_provider == "outlook":
        email_config = EmailConfig.outlook_config(
            email="your_email@outlook.com", password="your_password"
        )
    return email_config


