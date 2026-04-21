from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import SurveyPoint


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"})
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First name"})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last name"})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email")

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm password"})
    )


class SurveyPointForm(forms.ModelForm):
    class Meta:
        model = SurveyPoint
        fields = ("point_id", "description", "code", "notes", "northing", "easting", "elevation")
        widgets = {
            "point_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "PT-1042"}),
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Boundary Peg"}),
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "BND"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional note"}),
            "northing": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "easting": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "elevation": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
        }
