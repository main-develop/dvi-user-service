from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class CustomModelBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticates a user by username or email, overriding the base method.

        If an email is provided in **kwargs, attempts to retrieve the user by email.
        Otherwise, falls back to the username (or the model's USERNAME_FIELD).
        """

        email = kwargs.get("email")

        if email:
            try:
                user = UserModel._default_manager.get(email=email)
            except UserModel.DoesNotExist:
                # Run the default password hasher once to reduce the timing
                # difference between an existing and a nonexistent user (#20760).
                UserModel().set_password(password)
                return None
        else:
            if username is None:
                username = kwargs.get(UserModel.USERNAME_FIELD)
            try:
                user = UserModel._default_manager.get_by_natural_key(username)
            except UserModel.DoesNotExist:
                UserModel().set_password(password)
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    async def aauthenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticates a user by username or email, overriding the base method.
        Asynchronous version.

        If an email is provided in **kwargs, attempts to retrieve the user by email.
        Otherwise, falls back to the username (or the model's USERNAME_FIELD).
        """
        email = kwargs.get("email")

        if email:
            try:
                user = await UserModel._default_manager.aget(email=email)
            except UserModel.DoesNotExist:
                # Run the default password hasher once to reduce the timing
                # difference between an existing and a nonexistent user (#20760).
                UserModel().set_password(password)
                return None
        else:
            if username is None:
                username = kwargs.get(UserModel.USERNAME_FIELD)
            try:
                user = await UserModel._default_manager.aget_by_natural_key(username)
            except UserModel.DoesNotExist:
                UserModel().set_password(password)
                return None

        if await user.acheck_password(password) and self.user_can_authenticate(user):
            return user

        return None
