from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import NicheProfile, Community

class NicheRegistrationForm(UserCreationForm):
    """
    Registration form for niche dating users
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

class NicheLoginForm(forms.Form):
    """
    Login form for niche dating users
    """
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class NicheProfileForm(forms.ModelForm):
    """
    Form for creating and updating niche profiles
    """
    class Meta:
        model = NicheProfile
        exclude = ['user', 'communities', 'social_media_links', 'created_at', 'updated_at']
        widgets = {
            'interest_description': forms.Textarea(attrs={'rows': 4}),
            'interest_based_preferences': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make fields optional for initial setup
        for field in self.fields:
            self.fields[field].required = False

class CommunityForm(forms.ModelForm):
    """
    Form for creating and suggesting new communities
    """
    class Meta:
        model = Community
        fields = ['name', 'description', 'icon_class']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Community.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("A community with this name already exists.")
        return name 