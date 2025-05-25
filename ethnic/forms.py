from django import forms
from .models import EthnicProfile, Ethnicity, Language

class EthnicProfileForm(forms.ModelForm):
    # Use ModelMultipleChoiceField for ManyToMany relationships for better widget rendering by default
    ethnicities = forms.ModelMultipleChoiceField(
        queryset=Ethnicity.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select one or more ethnicities that you identify with."
    )
    languages_spoken = forms.ModelMultipleChoiceField(
        queryset=Language.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Languages you speak fluently."
    )
    partner_ethnicity_preference = forms.ModelMultipleChoiceField(
        queryset=Ethnicity.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Ethnicities you are interested in for a partner."
    )
    partner_language_preference = forms.ModelMultipleChoiceField(
        queryset=Language.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Languages you'd prefer your partner to speak."
    )

    class Meta:
        model = EthnicProfile
        fields = [
            'ethnicities', 
            'home_country', 
            'languages_spoken', 
            'cultural_values_description',
            'partner_ethnicity_preference',
            'partner_language_preference',
        ]
        widgets = {
            'cultural_values_description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: Add any custom initialization, like ordering queryset for choice fields
        # For example, self.fields['ethnicities'].queryset = Ethnicity.objects.order_by('name')
        # (This would require Ethnicity model to be populated first to be meaningful for users)
