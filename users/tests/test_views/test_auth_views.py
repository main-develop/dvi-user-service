import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status


@pytest.mark.django_db
def test_login_success(api_client, user):
    user.deletion_scheduled_at = timezone.now() + timezone.timedelta(hours=1)
    user.save()

    data = {
        "username_or_email": user.email,
        "password": "testpassword123",
        "remember_me": False,
    }
    response = api_client.post(path=reverse("auth_login"), data=data, format="json")

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.deletion_scheduled_at is None


@pytest.mark.django_db
def test_login_invalid_credentials(api_client):
    data = {"username_or_email": "wrong", "password": "wrong"}
    response = api_client.post(path=reverse("auth_login"), data=data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["errors"][0]["code"] == "invalid_credentials"


@pytest.mark.django_db
def test_logout(authenticated_client):
    response = authenticated_client.post(path=reverse("auth_logout"))
    assert response.status_code == status.HTTP_200_OK
