from django import forms
from django.contrib.auth import authenticate

from .models import Contestant, Answer


class NewUserForm(forms.ModelForm):
    error_messages = {
        'password_mismatch': 'The two password fields did not match.'
    }
    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Password'})
    )

    password2 = forms.CharField(
        label='Confirm Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = Contestant
        fields = ['username', 'name', 'email', 'college']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'name': forms.TextInput(attrs={'placeholder': 'Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'college': forms.TextInput(attrs={'placeholder': 'College'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        print(f'password1 = {password1}, password2 = {password2} and {password1 == password2}')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.save()
        return user


class PasswordResetForm(forms.Form):
    error_messages = {
        'password_mismatch': 'The two password fields did not match.'
    }
    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'New Password'})
    )

    password2 = forms.CharField(
        label='Confirm Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Confirm Password'})
    )

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text']


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={'autofocus': True, 'autocapitalize': 'none', 'autocomplete': 'username', 'placeholder': 'Username'})
    )

    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Password'}),
        strip=False
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username is not None and password is not None:
            self.user = authenticate(self.request, username=username, password=password)
            if not self.user:
                raise forms.ValidationError(
                    'Invalid username/password combination',
                    code='invalid_login'
                )

        return self.cleaned_data
