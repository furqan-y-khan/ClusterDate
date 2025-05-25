from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import LGBTQProfile

class LGBTQRegistrationForm(UserCreationForm):
    """
    Registration form for LGBTQ+ dating users
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

class LGBTQLoginForm(forms.Form):
    """
    Login form for LGBTQ+ dating users
    """
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class LGBTQProfileForm(forms.ModelForm):
    """
    Form for creating and updating LGBTQ+ profiles
    """
    class Meta:
        model = LGBTQProfile
        exclude = ['user']
        widgets = {
            'coming_out_story': forms.Textarea(attrs={'rows': 4}),
            'community_roles': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make fields optional for initial setup
        for field in self.fields:
            self.fields[field].required = False
        
        # Handle custom pronouns field visibility
        instance = kwargs.get('instance')
        if instance and instance.pronouns != 'CUSTOM':
            self.fields['custom_pronouns'].widget = forms.HiddenInput()
        
        # Add JavaScript to show/hide custom pronouns field
        self.fields['pronouns'].widget.attrs.update({
            'onchange': 'toggleCustomPronouns(this.value)'
        }) 