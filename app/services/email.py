"""Tiny email helper over Gmail SMTP (stdlib only).

Sending is best-effort: if SMTP isn't configured (no user/password in .env) or a
send fails, we log and move on rather than breaking the request that triggered
it. Call these from a FastAPI BackgroundTask so the HTTP response isn't blocked.
"""
import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings


def send_email(to: str, subject: str, body: str) -> None:
    """Send a plaintext email. No-op (with a log line) if email is disabled."""
    if not settings.emails_enabled:
        print(f"\n{'='*50}\n[email] disabled — intercepting email to {to}\nSUBJECT: {subject}\n\n{body}\n{'='*50}\n")
        return
    msg = EmailMessage()
    msg["From"] = settings.email_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls(context=ctx)
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
    except Exception as e:  # noqa: BLE001 — never let email break the caller
        pass


def send_welcome_email(*, to: str, full_name: str, role: str, password: str) -> None:
    """Welcome a newly-provisioned user with their login details."""
    login_url = f"{settings.app_base_url}/login"
    role_label = {"teacher": "Teacher", "parent": "Parent"}.get(role, role.title())
    body = (
        f"Hi {full_name},\n\n"
        f"A CampOS {role_label} account has been created for you.\n\n"
        f"Sign in here: {login_url}\n"
        f"  Email:    {to}\n"
        f"  Password: {password}\n\n"
        f"Please sign in and change your password from your profile.\n\n"
        f"— CampOS"
    )
    send_email(to, f"Your CampOS {role_label} account", body)
