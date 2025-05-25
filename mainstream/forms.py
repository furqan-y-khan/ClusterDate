from django import forms
from .models import MainstreamProfile
from django.utils.translation import gettext_lazy as _

class MainstreamProfileForm(forms.ModelForm):
    """
    Form for creating and updating a mainstream dating profile
    """
    class Meta:
        model = MainstreamProfile
        fields = [
            'relationship_status', 'looking_for', 'education_level', 
            'occupation', 'interested_in_gender', 'has_children', 
            'wants_children', 'smoker', 'drinker', 
            'photo_1', 'photo_2', 'photo_3', 'photo_4'
        ]
        widgets = {
            'relationship_status': forms.Select(attrs={'class': 'form-control'}),
            'looking_for': forms.Select(attrs={'class': 'form-control'}),
            'education_level': forms.Select(attrs={'class': 'form-control'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'interested_in_gender': forms.Select(attrs={'class': 'form-control'}, 
                                               choices=(('M', _('Male')), ('F', _('Female')), ('NB', _('Non-Binary')), ('O', _('Other')))),
            'has_children': forms.NullBooleanSelect(attrs={'class': 'form-control'}),
            'wants_children': forms.NullBooleanSelect(attrs={'class': 'form-control'}),
            'smoker': forms.NullBooleanSelect(attrs={'class': 'form-control'}),
            'drinker': forms.NullBooleanSelect(attrs={'class': 'form-control'}),
            'photo_1': forms.FileInput(attrs={'class': 'form-control-file'}),
            'photo_2': forms.FileInput(attrs={'class': 'form-control-file'}),
            'photo_3': forms.FileInput(attrs={'class': 'form-control-file'}),
            'photo_4': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
        
    def clean_photo_1(self):
        photo = self.cleaned_data.get('photo_1')
        if photo:
            if photo.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError(_('Image file too large ( > 5MB )'))
        return photo
        
    def clean_photo_2(self):
        photo = self.cleaned_data.get('photo_2')
        if photo:
            if photo.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError(_('Image file too large ( > 5MB )'))
        return photo
        
    def clean_photo_3(self):
        photo = self.cleaned_data.get('photo_3')
        if photo:
            if photo.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError(_('Image file too large ( > 5MB )'))
        return photo
        
    def clean_photo_4(self):
        photo = self.cleaned_data.get('photo_4')
        if photo:
            if photo.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError(_('Image file too large ( > 5MB )'))
        return photo


class MainstreamProfileSearchForm(forms.Form):
    """
    Form for searching profiles with filters
    """
    GENDER_CHOICES = [
        ('', _('Any')),
        ('M', _('Male')),
        ('F', _('Female')),
        ('NB', _('Non-Binary')),
        ('O', _('Other')),
    ]
    
    RELATIONSHIP_STATUS_CHOICES = [('', _('Any'))] + list(MainstreamProfile.RELATIONSHIP_STATUS_CHOICES)
    LOOKING_FOR_CHOICES = [('', _('Any'))] + list(MainstreamProfile.LOOKING_FOR_CHOICES)
    EDUCATION_LEVEL_CHOICES = [('', _('Any'))] + list(MainstreamProfile.EDUCATION_LEVEL_CHOICES)
    
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    min_age = forms.IntegerField(
        required=False,
        min_value=18,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Min Age')})
    )
    
    max_age = forms.IntegerField(
        required=False,
        min_value=18,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Max Age')})
    )
    
    relationship_status = forms.ChoiceField(
        choices=RELATIONSHIP_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    looking_for = forms.ChoiceField(
        choices=LOOKING_FOR_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    education_level = forms.ChoiceField(
        choices=EDUCATION_LEVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    distance = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=500,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Distance (km)')})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        min_age = cleaned_data.get('min_age')
        max_age = cleaned_data.get('max_age')
        
        if min_age and max_age and min_age > max_age:
            raise forms.ValidationError(_('Minimum age cannot be greater than maximum age'))
            
        return cleaned_data 