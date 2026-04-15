from unittest.mock import patch

import pytest

from users.emails import EmailPurpose, send_email


@pytest.mark.django_db
def test_send_email_includes_otp_for_account_activation(user):
    with patch("users.emails.generate_and_set_otp") as mock_otp:
        mock_otp.return_value = "ABC123"

        send_email(EmailPurpose.ACCOUNT_ACTIVATION, to=user.email)

        mock_otp.assert_called_once_with(email=user.email)
