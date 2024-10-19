from django import forms
from django.contrib.auth.forms import UserCreationForm
from userauths.models import User  

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    telegram_id = forms.CharField(max_length=50, required=True)

    class Meta:
        model = User  
        fields = ['username', 'email', 'telegram_id', 'password1', 'password2']
