from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import SugarProfile

class SugarRegistrationForm(UserCreationForm):
    """
    Registration form for sugar dating users
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

class SugarLoginForm(forms.Form):
    """
    Login form for sugar dating users
    """
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class SugarProfileForm(forms.ModelForm):
    """
    Form for creating and updating sugar profiles
    """
    class Meta:
        model = SugarProfile
        exclude = ['user', 'is_sugar_daddy', 'is_sugar_mommy', 'is_sugar_baby', 
                  'is_income_verified', 'is_background_checked', 'background_check_date']
        widgets = {
            'allowance_expectations': forms.Textarea(attrs={'rows': 3}),
            'travel_preferences': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make fields optional for initial setup
        for field in self.fields:
            self.fields[field].required = False
        
        # Customize field labels
        self.fields['income_range'].label = "Income Range"
        self.fields['net_worth_range'].label = "Net Worth Range"
        self.fields['lifestyle'].label = "Lifestyle"
        self.fields['relationship_type'].label = "Preferred Relationship Type"
        self.fields['allowance_expectations'].label = "Allowance Expectations"
        self.fields['travel_preferences'].label = "Travel Preferences" 