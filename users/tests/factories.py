import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"testuser{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.django.Password("testpassword123")
    is_active = True
