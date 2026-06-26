"""
Email service — sends OTP emails via SMTP.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config.settings import settings


def send_otp_email(to_email: str, otp: str) -> None:
    """Send a 6-digit OTP verification email to the user using SMTP."""
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
        <h2 style="color: #4f46e5;">🎓 HCAI-ITS Email Verification</h2>
        <p>Use the code below to verify your email address. It expires in <strong>10 minutes</strong>.</p>
        <div style="
            font-size: 36px;
            font-weight: bold;
            letter-spacing: 12px;
            text-align: center;
            padding: 24px;
            background: #f1f0ff;
            border-radius: 12px;
            color: #4f46e5;
            margin: 24px 0;
        ">
            {otp}
        </div>
        <p style="color: #6b7280; font-size: 14px;">
            If you did not create an account, you can safely ignore this email.
        </p>
    </div>
    """

    # Ensure SMTP settings are configured
    if not settings.smtp_username or not settings.smtp_password:
        raise ValueError(
            "SMTP is not configured. Please set SMTP_USERNAME and SMTP_PASSWORD in your backend/.env file."
        )

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your HCAI-ITS Verification Code"
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email or settings.smtp_username}>"
        msg["To"] = to_email

        part = MIMEText(html_content, "html")
        msg.attach(part)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_port == 587:
                server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(
                settings.smtp_from_email or settings.smtp_username,
                [to_email],
                msg.as_string()
            )

        print(f"[SMTP] OK: Verification email sent to {to_email}")
    except Exception as e:
        print(f"[SMTP] ERROR: Delivery failed to {to_email}. Error: {e}")
        raise ValueError(f"Failed to send email verification: {e}")
