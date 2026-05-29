"""
Email service — sends OTP emails via Resend.
"""
import resend

from app.config.settings import settings

resend.api_key = settings.resend_api_key

_FROM_ADDRESS = "onboarding@resend.dev"   # Resend's free sandbox sender (works without a custom domain)


def send_otp_email(to_email: str, otp: str) -> None:
    """Send a 6-digit OTP verification email to the user."""
    resend.Emails.send({
        "from": _FROM_ADDRESS,
        "to": [to_email],
        "subject": "Your HCAI-ITS Verification Code",
        "html": f"""
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
        """,
    })
