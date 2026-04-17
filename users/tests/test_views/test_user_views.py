import pytest
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from djoser import utils
from rest_framework import status

from users.services.otp import generate_and_set_otp


@pytest.mark.django_db
def test_user_perform_create(api_client):
    data = {
        "email": "test@example.com",
        "username": "test_user",
        "password": "testpassword123",
        "confirm_password": "testpassword123",
    }
    response = api_client.post(path=reverse("auth_register"), data=data, format="json")

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_user_perform_create_password_too_long(api_client):
    data = {
        "email": "test@example.com",
        "username": "test_user",
        "password": "password_is_way_too_long",
        "confirm_password": "password_is_way_too_long",
    }
    response = api_client.post(path=reverse("auth_register"), data=data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["errors"][0]["code"] == "password_too_long"


@pytest.mark.parametrize(
    "purpose",
    ["account_activation", "change_email", "reset_password"],
)
@pytest.mark.django_db
def test_user_resend_verification_email(api_client, user, purpose):
    if purpose == "account_activation":
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
        "purpose": "account_activation",
    }
    response = api_client.post(path=reverse("auth_verify"), data=data, format="json")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    user.refresh_from_db()
    assert user.is_active


@pytest.mark.django_db
def test_user_change_email(authenticated_client, user):
    data = {"current_password": "testpassword123", "new_email": "new_test@example.com"}
    response = authenticated_client.post(
        path=reverse("users_me_email"), data=data, format="json"
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    user.refresh_from_db()
    assert user.pending_email == "new_test@example.com"


@pytest.mark.django_db
def test_user_verify_change_email(api_client, user):
    user.pending_email = "new_test@example.com"
    user.save()

    data = {
        "email": user.email,
        "otp": generate_and_set_otp(user.email),
        "purpose": "change_email",
    }
    response = api_client.post(path=reverse("auth_verify"), data=data, format="json")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    user.refresh_from_db()
    assert user.email == "new_test@example.com"
    assert user.pending_email is None


@pytest.mark.django_db
def test_user_verify_reset_password(api_client, user):
    data = {
        "email": user.email,
        "otp": generate_and_set_otp(user.email),
        "purpose": "reset_password",
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
        "new_password": "testpassword123",
        "confirm_password": "testpassword123",
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
        data={"current_password": "testpassword123"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.deletion_scheduled_at
