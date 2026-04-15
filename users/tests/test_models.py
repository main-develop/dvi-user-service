import pytest
from django.db.utils import IntegrityError
from factories import UserFactory


@pytest.mark.django_db(transaction=True)
def test_user_creation_and_constraints(transactional_user):
    assert transactional_user.pk is not None
    assert transactional_user.username
    assert transactional_user.email

    with pytest.raises(IntegrityError):
        UserFactory(username=transactional_user.username)

    with pytest.raises(IntegrityError):
        UserFactory(email=transactional_user.email)
