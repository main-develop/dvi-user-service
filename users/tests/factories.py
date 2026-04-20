from enum import StrEnum

import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class TestData(StrEnum):
    USERNAME = "test_user"
    EMAIL = "test@example.com"
    NEW_EMAIL = "new_test@example.com"
    PASSWORD = "strOng5assWorD"
    LONG_PASSWORD = (
        "password_is_way_too_long_password_is_way_too_long_password_is_way_t"
    )


USER_CREATE_DATA = {
    "username": TestData.USERNAME,
    "email": TestData.EMAIL,
    "password": TestData.PASSWORD,
    "confirm_password": TestData.PASSWORD,
}


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"testuser{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.django.Password(TestData.PASSWORD)
    is_active = True
