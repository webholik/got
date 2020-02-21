import random
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Contest(models.Model):
    start_time = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.pk and self.objects.exists():
            raise ValidationError("There can only be one contest")
        return super().save(*args, **kwargs)


class Question(models.Model):
    number = models.IntegerField()
    text = models.TextField(max_length=1500)
    image = models.ImageField(blank=True)
    correct_answer = models.CharField(max_length=500)
    answer_description = models.TextField(blank=True)
    # release_date = models.DateTimeField()
    points = models.IntegerField()

    def __str__(self):
        return f"Question {self.number}"

    def time_since(self):
        diff = timezone.now() - self.release_date
        if diff.days > 0:
            return f'{diff.days} days'
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            ret = f'{hours} hour'
            if hours != 1:
                return ret + 's'
            return ret
        else:
            minutes = diff.seconds // 60
            ret = f'{minutes} minute'
            if minutes != 1:
                return ret + 's'
            return ret


class CustomManager(UserManager):
    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_active', True)
        return super().create_superuser(username, email, password, **extra_fields)


class Contestant(AbstractBaseUser):
    username = models.CharField(
        max_length=100,
        unique=True,
        primary_key=True,
        validators=[UnicodeUsernameValidator()],
        error_messages={
            'unique': 'A contestant with that username already exists'
        }
    )

    email = models.EmailField(
        unique=True,
        error_messages={
            'unique': 'A contestant with that email already exists'
        }
    )

    name = models.CharField(max_length=100)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    college = models.CharField(max_length=100)
    points = models.IntegerField(default=0)
    extra_time = models.DurationField(default=timedelta(0))
    answered_questions = models.ManyToManyField(Question, blank=True)

    objects = CustomManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    def get_extra_time(self):
        hours, rest = divmod(self.extra_time.seconds, 3600)
        hours += self.extra_time.days * 24
        minutes, seconds = divmod(rest, 60)
        return f'{hours}:{minutes}:{seconds}'

    def unread_messages(self):
        return self.message_set.filter(seen=False)

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.username

    def clean(self):
        super().clean()
        self.email = UserManager.normalize_email(self.email)

    def has_perm(self, perm, obj=None):
        print(f'has_perm called with {perm} and obj={obj}')
        return self.is_staff

    def has_module_perms(self, app_label):
        print(f'has_module_perms called {app_label}')
        return self.is_staff


class Answer(models.Model):
    text = models.CharField(max_length=500)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    contestant = models.ForeignKey(Contestant, on_delete=models.CASCADE)
    time = models.DateTimeField()

    def __str__(self):
        return 'Answer'


class Hint(models.Model):
    text = models.CharField(max_length=500, blank=True)
    image = models.ImageField(blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    release_date = models.DateTimeField()


def generate_random_string():
    chars = 'abcdefghijklmnopqrstuvwxyz1234567890'
    random_str = ''
    for i in range(30):
        random_str += random.choice(chars)

    return random_str


class AbstractHashModel(models.Model):
    hash = models.CharField(default=generate_random_string, max_length=30)
    contestant = models.ForeignKey(Contestant, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.contestant.username}:{self.hash}'

    class Meta:
        abstract = True


class ActivationModel(AbstractHashModel):
    pass


class PasswordResetModel(AbstractHashModel):
    pass


class Message(models.Model):
    text = models.TextField()
    seen = models.BooleanField(default=False)
    contestant = models.ForeignKey(to=Contestant, on_delete=models.CASCADE)
