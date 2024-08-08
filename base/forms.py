from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Room, User


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['name', 'username', 'email', 'password1', 'password2']


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = '__all__'
        exclude = ['host', 'participants']


class UserForm(forms.ModelForm):
    birth_date = forms.DateField(label= "Birthday", widget=forms.DateInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Expiration', 'type': 'date'}), required=True)
    
    class Meta:
        model = User
        fields = ['avatar', 'name', 'username', 'email', 'bio', 'birth_date']
