from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.contrib.auth import login

class AuthBackend(ModelBackend):
    def authenticate(self, email, password):
        model = get_user_model()
        try:
            user = model.objects.get(email=email)
        except model.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
            return None

