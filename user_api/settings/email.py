from .base import env

DJOSER = {
    "SEND_ACTIVATION_EMAIL": True,
    "SEND_CONFIRMATION_EMAIL": True,
    "ACTIVATION_URL": "#/activate/{uid}/{token}",
    "USER_CREATE_PASSWORD_RETYPE": True,
    "SET_PASSWORD_RETYPE": True,
    "PASSWORD_RESET_CONFIRM_RETYPE": True,
    "PASSWORD_CHANGED_EMAIL_CONFIRMATION": True,
    "PASSWORD_RESET_CONFIRM_URL": "#/password-reset/{uid}/{token}",
    "EMAIL": {
        "activation": "users.emails.CustomActivationEmail",
        "confirmation": "users.emails.CustomConfirmationEmail",
        "password_reset": "users.emails.PasswordResetEmail",
        "password_changed_confirmation": "users.emails.CustomPasswordChangedConfirmationEmail",
    },
    "SERIALIZERS": {
        "activation": "users.serializers.ActivationSerializer",
        "set_username": "users.serializers.CustomSetUsernameSerializer",
        "password_reset": "users.serializers.CustomSendEmailResetSerializer",
        "password_reset_confirm_retype": "users.serializers.PasswordResetConfirmRetypeSerializer",
        "set_password_retype": "users.serializers.SetPasswordRetypeSerializer",
        "user_create_password_retype": "users.serializers.CustomUserCreatePasswordRetypeSerializer",
        "user_delete": "users.serializers.CustomUserDeleteSerializer",
    },
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
