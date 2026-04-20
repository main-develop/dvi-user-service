import pytest
from factories import UserFactory
from rest_framework.test import APIClient, APIRequestFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def user_request(user):
    request = APIRequestFactory().post("/")
    request.user = user
    return request


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_login(user)
    return api_client
