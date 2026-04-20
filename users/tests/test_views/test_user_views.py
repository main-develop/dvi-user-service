import pytest
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from djoser import utils
from factories import USER_CREATE_DATA, TestData
from rest_framework import status

from users.serializers.user import VerificationPurpose
from users.services.otp import generate_and_set_otp


@pytest.mark.django_db
def test_user_perform_create(api_client):
    data = USER_CREATE_DATA.copy()
    response = api_client.post(path=reverse("auth_register"), data=data, format="json")

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_user_perform_create_password_too_long(api_client):
    data = {
        "username": TestData.USERNAME,
        "email": TestData.EMAIL,
        "password": TestData.LONG_PASSWORD,
        "confirm_password": TestData.LONG_PASSWORD,
    }
    response = api_client.post(path=reverse("auth_register"), data=data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["errors"][0]["code"] == "password_too_long"


@pytest.mark.django_db
def test_user_perform_create_password_too_weak(api_client):
    data = {
        "username": TestData.USERNAME,
        "email": TestData.EMAIL,
        "password": "weakkkkkkkkkk",
        "confirm_password": "weakkkkkkkkkk",
    }
    response = api_client.post(path=reverse("auth_register"), data=data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["errors"][0]["code"] == "password_too_weak"


@pytest.mark.django_db
def test_user_perform_create_password_compromised(api_client):
    data = {
        "username": TestData.USERNAME,
        "email": TestData.EMAIL,
        "password": "Admin!12345",
        "confirm_password": "Admin!12345",
    }
    response = api_client.post(path=reverse("auth_register"), data=data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["errors"][0]["code"] == "password_compromised"


@pytest.mark.parametrize(
    "purpose",
    [p.value for p in VerificationPurpose],
)
@pytest.mark.django_db
def test_user_resend_verification_email(api_client, user, purpose):
    if purpose == VerificationPurpose.ACCOUNT_ACTIVATION:
        user.is_active = False
        user.save()

    data = {"email": user.email, "purpose": purpose}
    response = api_client.post(
        path=reverse("auth_resend_verification_email"), data=data, format="json"
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_user_verify_account_activation(api_client, user):
    user.is_active = False
    user.save()

    data = {
        "email": user.email,
        "otp": generate_and_set_otp(user.email),
        "purpose": VerificationPurpose.ACCOUNT_ACTIVATION,
    }
    response = api_client.post(path=reverse("auth_verify"), data=data, format="json")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    user.refresh_from_db()
    assert user.is_active


@pytest.mark.django_db
def test_user_change_email(authenticated_client, user):
    data = {"current_password": TestData.PASSWORD, "new_email": TestData.NEW_EMAIL}
    response = authenticated_client.post(
        path=reverse("users_me_email"), data=data, format="json"
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    user.refresh_from_db()
    assert user.pending_email == TestData.NEW_EMAIL


@pytest.mark.django_db
def test_user_verify_change_email(api_client, user):
    user.pending_email = TestData.NEW_EMAIL
    user.save()

    data = {
        "email": user.email,
        "otp": generate_and_set_otp(user.email),
        "purpose": VerificationPurpose.CHANGE_EMAIL,
    }
    response = api_client.post(path=reverse("auth_verify"), data=data, format="json")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    user.refresh_from_db()
    assert user.email == TestData.NEW_EMAIL
    assert user.pending_email is None


@pytest.mark.django_db
def test_user_verify_reset_password(api_client, user):
    data = {
        "email": user.email,
        "otp": generate_and_set_otp(user.email),
        "purpose": VerificationPurpose.RESET_PASSWORD,
    }
    response = api_client.post(path=reverse("auth_verify"), data=data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["uid"] and response.data["token"]


@pytest.mark.django_db
def test_user_reset_password(api_client, user):
    response = api_client.post(
        path=reverse("users_password_reset"), data={"email": user.email}, format="json"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_user_reset_password_confirm(api_client, user):
    data = {
        "uid": utils.encode_uid(user.pk),
        "token": default_token_generator.make_token(user),
        "new_password": TestData.PASSWORD,
        "confirm_password": TestData.PASSWORD,
    }
    response = api_client.post(
        path=reverse("users_password_reset_confirm"), data=data, format="json"
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    user.refresh_from_db()
    assert user.has_usable_password()


@pytest.mark.django_db
def test_user_lockdown(api_client, user):
    data = {
        "uid": utils.encode_uid(user.pk),
        "token": default_token_generator.make_token(user),
    }
    response = api_client.post(
        path=reverse("users_account_security_lockdown"), data=data, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert not user.has_usable_password()
    assert user.deletion_scheduled_at is None
    assert user.pending_email is None


@pytest.mark.django_db
def test_user_destroy(authenticated_client, user):
    response = authenticated_client.delete(
        path=reverse("users_me"),
        data={"current_password": TestData.PASSWORD},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.deletion_scheduled_at
