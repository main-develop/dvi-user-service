from .base import env

DJOSER = {
    "SEND_ACTIVATION_EMAIL": True,
    "SEND_CONFIRMATION_EMAIL": True,
    "USER_CREATE_PASSWORD_RETYPE": True,
    "SET_PASSWORD_RETYPE": True,
    "PASSWORD_RESET_CONFIRM_RETYPE": True,
    "PASSWORD_CHANGED_EMAIL_CONFIRMATION": True,
    "EMAIL": {
        "activation": "users.emails.AccountActivationEmail",
        "confirmation": "users.emails.AccountActivatedEmail",
        "password_reset": "users.emails.PasswordResetEmail",
        "password_changed_confirmation": "users.emails.PasswordChangedEmail",
    },
    "SERIALIZERS": {
        "set_username": "users.serializers.user.SetUsernameSerializer",
        "password_reset": "users.serializers.user.PasswordResetSerializer",
        "password_reset_confirm_retype": "users.serializers.user.PasswordResetConfirmSerializer",
        "set_password_retype": "users.serializers.user.SetPasswordRetypeSerializer",
        "user_create_password_retype": "users.serializers.user.UserCreatePasswordRetypeSerializer",
        "user_delete": "users.serializers.user.UserDeleteSerializer",
    },
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
