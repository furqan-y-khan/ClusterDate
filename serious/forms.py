from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import SeriousProfile

class SeriousRegistrationForm(UserCreationForm):
    """
    Registration form for serious dating users
    """
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        
        return user

class SeriousLoginForm(forms.Form):
    """
    Login form for serious dating users
    """
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class SeriousProfileForm(forms.ModelForm):
    """
    Form for creating and updating serious relationship profiles
    """
    class Meta:
        model = SeriousProfile
        exclude = ['user']
        widgets = {
            'about_me': forms.Textarea(attrs={'rows': 4}),
            'looking_for': forms.Textarea(attrs={'rows': 4}),
            'relationship_goals': forms.Textarea(attrs={'rows': 3}),
            'deal_breakers': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make fields optional for initial setup
        for field in self.fields:
            self.fields[field].required = False 