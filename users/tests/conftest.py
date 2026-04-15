import pytest
from factories import UserFactory
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def transactional_user(transactional_db):
    return UserFactory()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_login(user)
    return api_client
