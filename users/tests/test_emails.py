from unittest.mock import patch

import pytest
from django.core import mail

from users.emails import EmailPurpose, send_email

OTP_BASED_PURPOSES = {
    EmailPurpose.ACCOUNT_ACTIVATION,
    EmailPurpose.CHANGE_EMAIL,
    EmailPurpose.RESET_PASSWORD,
}


@pytest.mark.parametrize("purpose", OTP_BASED_PURPOSES)
@pytest.mark.django_db
def test_send_email_calls_generate_otp_for_otp_based_purposes(user, purpose):
    with patch("users.emails.generate_and_set_otp") as mock_otp:
        mock_otp.return_value = "ABC123"

        send_email(purpose, to=user.email)

        mock_otp.assert_called_once_with(email=user.email)


def test_send_email_no_user():
    send_email(
        EmailPurpose.EMAIL_CHANGED_NOTICE, context={"uid": "", "token": ""}, to=""
    )
    assert len(mail.outbox) == 0
