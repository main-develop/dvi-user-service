import pytest
from rest_framework.test import APIRequestFactory

from users.serializers.user import (
    ChangeEmailSerializer,
    SetPasswordRetypeSerializer,
    UserCreatePasswordRetypeSerializer,
)

USER_CREATE_DATA = {
    "username": "test_user",
    "email": "test@example.com",
    "password": "testpassword123",
    "confirm_password": "testpassword123",
}


@pytest.mark.django_db
def test_user_create_password_retype_serializer_valid():
    data = USER_CREATE_DATA.copy()
    serializer = UserCreatePasswordRetypeSerializer(data=data)

    assert serializer.is_valid()
    assert "confirm_password" not in serializer.validated_data


@pytest.mark.django_db
def test_user_create_password_retype_serializer_mismatch():
    data = {**USER_CREATE_DATA, "confirm_password": "mismatch"}
    serializer = UserCreatePasswordRetypeSerializer(data=data)

    assert not serializer.is_valid()
    assert serializer.errors["non_field_errors"][0].code == "password_mismatch"


@pytest.mark.django_db
def test_set_password_retype_serializer_valid(user):
    factory = APIRequestFactory()
    request = factory.post("/")
    request.user = user

    data = {
        "new_password": "testpassword123",
        "confirm_password": "testpassword123",
        "current_password": "testpassword123",
    }

    serializer = SetPasswordRetypeSerializer(data=data, context={"request": request})

    assert serializer.is_valid()
    assert "confirm_password" not in serializer.validated_data


@pytest.mark.django_db
def test_set_password_retype_serializer_mismatch(user):
    factory = APIRequestFactory()
    request = factory.post("/")
    request.user = user

    data = {
        "new_password": "testpassword123",
        "confirm_password": "invalid",
        "current_password": "testpassword123",
    }

    serializer = SetPasswordRetypeSerializer(data=data, context={"request": request})

    assert not serializer.is_valid()
    assert serializer.errors["non_field_errors"][0].code == "password_mismatch"


@pytest.mark.django_db
def test_change_email_serializer_valid(user):
    factory = APIRequestFactory()
    request = factory.post("/")
    request.user = user

    data = {"current_password": "testpassword123", "new_email": "new_test@example.com"}
    serializer = ChangeEmailSerializer(data=data, context={"request": request})

    assert serializer.is_valid()
    assert serializer.validated_data["new_email"] == "new_test@example.com"


@pytest.mark.django_db
def test_change_email_serializer_invalid_password(user):
    factory = APIRequestFactory()
    request = factory.post("/")
    request.user = user

    data = {"current_password": "invalid", "new_email": "new_test@example.com"}
    serializer = ChangeEmailSerializer(data=data, context={"request": request})

    assert not serializer.is_valid()
    assert serializer.errors["current_password"][0].code == "invalid_password"


@pytest.mark.django_db
def test_change_email_serializer_invalid_email(user):
    factory = APIRequestFactory()
    request = factory.post("/")
    request.user = user

    serializer = ChangeEmailSerializer(
        data={"current_password": "testpassword123", "new_email": user.email},
        context={"request": request},
    )

    assert not serializer.is_valid()
    assert serializer.errors["new_email"][0].code == "invalid"
