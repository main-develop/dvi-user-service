from celery import shared_task

from users.emails import EmailPurposeLiteral, send_email


@shared_task
def send_email_task(
    purpose: EmailPurposeLiteral, to: str, context: dict | None = None
) -> None:
    """Async email sender."""
    send_email(purpose=purpose, to=to, context=context)
