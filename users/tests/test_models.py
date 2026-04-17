import pytest
from django.db.utils import IntegrityError
from factories import UserFactory


@pytest.mark.django_db
def test_user_creation(user):
    assert user.pk is not None
    assert user.username
    assert user.email


@pytest.mark.django_db
def test_user_username_must_be_unique(user):
    with pytest.raises(IntegrityError):
        UserFactory(username=user.username)


@pytest.mark.django_db
def test_user_email_must_be_unique(user):
    with pytest.raises(IntegrityError):
        UserFactory(email=user.email)
