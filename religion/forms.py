from django import forms
from .models import ReligionProfile


class ReligionProfileForm(forms.ModelForm):
    """
    Form for creating and updating religion profiles
    """
    
    class Meta:
        model = ReligionProfile
        exclude = ['user']
        widgets = {
            'religious_values': forms.Textarea(attrs={'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values for denomination field based on selected religion
        instance = kwargs.get('instance')
        if instance and instance.religion:
            self.fields['denomination'].widget = forms.Select(
                choices=[('', '---')] + ReligionProfile.DENOMINATION_CHOICES.get(instance.religion, [])
            )
        else:
            self.fields['denomination'].widget = forms.Select(choices=[('', '---')])
            
        # Same for preference fields
        if instance and instance.religion_preference:
            self.fields['denomination_preference'].widget = forms.Select(
                choices=[('', '---')] + ReligionProfile.DENOMINATION_CHOICES.get(instance.religion_preference, [])
            )
        else:
            self.fields['denomination_preference'].widget = forms.Select(choices=[('', '---')])
        
        # Add dependency between fields
        self.fields['religion'].widget.attrs.update({
            'onchange': 'updateDenominationOptions(this.value, "id_denomination")'
        })
        self.fields['religion_preference'].widget.attrs.update({
            'onchange': 'updateDenominationOptions(this.value, "id_denomination_preference")'
        })


class DenominationChoiceField(forms.ChoiceField):
    """
    A dynamic choice field that updates based on the selected religion
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('choices', [('', '---')])
        super().__init__(*args, **kwargs)
        
    def update_choices(self, religion_code):
        """Update choices based on religion code"""
        choices = [('', '---')]
        if religion_code in ReligionProfile.DENOMINATION_CHOICES:
            choices.extend(ReligionProfile.DENOMINATION_CHOICES[religion_code])
        self.choices = choices 