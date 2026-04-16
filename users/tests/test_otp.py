import pytest
from django.core.cache import cache
from rest_framework.exceptions import ValidationError

from users.services.otp import generate_and_set_otp, verify_otp


@pytest.mark.django_db
def test_generate_and_set_otp(user):
    otp = generate_and_set_otp(user.email)

    assert len(otp) == 6
    assert otp == cache.get(f"otp_{user.email}")


@pytest.mark.django_db
def test_verify_otp_success(user):
    otp = generate_and_set_otp(user.email)
    verified_user = verify_otp(user.email, otp)

    assert verified_user == user
    assert cache.get(f"otp_{user.email}") is None  # must be cleaned up


@pytest.mark.django_db
def test_verify_otp_expired_otp(user):
    with pytest.raises(ValidationError) as exc:
        verify_otp(user.email, "123ABC")

    assert "otp" in exc.value.detail


@pytest.mark.django_db
def test_verify_otp_invalid_otp(user):
    generate_and_set_otp(user.email)

    with pytest.raises(ValidationError) as exc:
        verify_otp(user.email, "123ABC")

    assert "otp" in exc.value.detail


@pytest.mark.django_db
def test_verify_otp_user_does_not_exist(user):
    otp = generate_and_set_otp("non-existent@example.com")

    with pytest.raises(ValidationError) as exc:
        verify_otp("non-existent@example.com", otp)

    assert "email" in exc.value.detail
