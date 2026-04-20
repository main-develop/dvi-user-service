import pytest
from factories import USER_CREATE_DATA, TestData, UserFactory

from users.serializers.user import (
    ChangeEmailSerializer,
    SetPasswordRetypeSerializer,
    UserCreatePasswordRetypeSerializer,
)


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
def test_set_password_retype_serializer_valid(user_request):
    data = {
        "new_password": TestData.PASSWORD,
        "confirm_password": TestData.PASSWORD,
        "current_password": TestData.PASSWORD,
    }

    serializer = SetPasswordRetypeSerializer(
        data=data, context={"request": user_request}
    )

    assert serializer.is_valid()
    assert "confirm_password" not in serializer.validated_data


@pytest.mark.django_db
def test_set_password_retype_serializer_mismatch(user_request):
    data = {
        "new_password": TestData.PASSWORD,
        "confirm_password": "invalid",
        "current_password": TestData.PASSWORD,
    }

    serializer = SetPasswordRetypeSerializer(
        data=data, context={"request": user_request}
    )

    assert not serializer.is_valid()
    assert serializer.errors["non_field_errors"][0].code == "password_mismatch"


@pytest.mark.django_db
def test_change_email_serializer_valid(user_request):
    data = {"current_password": TestData.PASSWORD, "new_email": TestData.NEW_EMAIL}
    serializer = ChangeEmailSerializer(data=data, context={"request": user_request})

    assert serializer.is_valid()
    assert serializer.validated_data["new_email"] == TestData.NEW_EMAIL


@pytest.mark.django_db
def test_change_email_serializer_invalid_password(user_request):
    data = {"current_password": "invalid", "new_email": TestData.NEW_EMAIL}
    serializer = ChangeEmailSerializer(data=data, context={"request": user_request})

    assert not serializer.is_valid()
    assert serializer.errors["current_password"][0].code == "invalid_password"


@pytest.mark.django_db
def test_change_email_serializer_invalid_email(user_request):
    serializer = ChangeEmailSerializer(
        data={
            "current_password": TestData.PASSWORD,
            "new_email": user_request.user.email,
        },
        context={"request": user_request},
    )

    assert not serializer.is_valid()
    assert serializer.errors["new_email"][0].code == "invalid"


@pytest.mark.django_db
def test_change_email_serializer_email_already_taken(user_request):
    other_user = UserFactory()

    serializer = ChangeEmailSerializer(
        data={"current_password": TestData.PASSWORD, "new_email": other_user.email},
        context={"request": user_request},
    )

    assert not serializer.is_valid()
    assert serializer.errors["new_email"][0].code == "invalid"
