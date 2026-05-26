"""
NutriScan — forms.py
=====================
All Django forms for NutriScan:
    - RegisterForm       : username + email + password + repeat
    - UserProfileForm    : body data, lifestyle, medical flags
    - FoodInputForm      : upload image / URL / text name + portion
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, FoodEntry, ActivityLevel, HealthGoal, BiologicalSex


# ══════════════════════════════════════════════════════════════════════════════
#  REGISTER
# ══════════════════════════════════════════════════════════════════════════════

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'your@email.com',
            'class': 'ns-input',
        })
    )
    first_name = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'First name (optional)',
            'class': 'ns-input',
        })
    )

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply consistent styling to all fields
        for field_name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'ns-input'
            field.widget.attrs.setdefault('autocomplete', 'off')

        self.fields['username'].widget.attrs['placeholder'] = 'Choose a username'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm password'
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        self.fields['username'].help_text  = None

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email      = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        if commit:
            user.save()
        return user


# ══════════════════════════════════════════════════════════════════════════════
#  USER PROFILE
# ══════════════════════════════════════════════════════════════════════════════

class UserProfileForm(forms.ModelForm):
    """
    Shown on first login (profile setup wizard) and on profile edit page.
    Split into logical sections via fieldsets in the template.
    """

    class Meta:
        model  = UserProfile
        fields = [
            # Body
            'age', 'biological_sex', 'height_cm', 'weight_kg',
            # Lifestyle
            'activity_level', 'health_goal',
            # Medical
            'has_diabetes', 'has_hypertension',
            'is_vegetarian', 'is_vegan',
            'is_gluten_free', 'is_lactose_free', 'has_nut_allergy',
        ]
        widgets = {
            'age': forms.NumberInput(attrs={
                'class': 'ns-input ns-input-sm',
                'placeholder': 'e.g. 28',
                'min': 10, 'max': 120,
            }),
            'height_cm': forms.NumberInput(attrs={
                'class': 'ns-input ns-input-sm',
                'placeholder': 'e.g. 175',
                'min': 50, 'max': 300,
                'step': '0.1',
            }),
            'weight_kg': forms.NumberInput(attrs={
                'class': 'ns-input ns-input-sm',
                'placeholder': 'e.g. 72.5',
                'min': 10, 'max': 500,
                'step': '0.1',
            }),
            'biological_sex': forms.Select(attrs={
                'class': 'ns-select',
            }),
            'activity_level': forms.Select(attrs={
                'class': 'ns-select',
            }),
            'health_goal': forms.Select(attrs={
                'class': 'ns-select',
            }),
            # Medical flags — render as styled checkboxes
            'has_diabetes':     forms.CheckboxInput(attrs={'class': 'ns-checkbox'}),
            'has_hypertension': forms.CheckboxInput(attrs={'class': 'ns-checkbox'}),
            'is_vegetarian':    forms.CheckboxInput(attrs={'class': 'ns-checkbox'}),
            'is_vegan':         forms.CheckboxInput(attrs={'class': 'ns-checkbox'}),
            'is_gluten_free':   forms.CheckboxInput(attrs={'class': 'ns-checkbox'}),
            'is_lactose_free':  forms.CheckboxInput(attrs={'class': 'ns-checkbox'}),
            'has_nut_allergy':  forms.CheckboxInput(attrs={'class': 'ns-checkbox'}),
        }
        labels = {
            'biological_sex' : 'Biological sex',
            'height_cm'      : 'Height (cm)',
            'weight_kg'      : 'Weight (kg)',
            'activity_level' : 'Activity level',
            'health_goal'    : 'Health goal',
            'has_diabetes'   : 'I have diabetes',
            'has_hypertension': 'I have hypertension',
            'is_vegetarian'  : 'Vegetarian',
            'is_vegan'       : 'Vegan',
            'is_gluten_free' : 'Gluten intolerant',
            'is_lactose_free': 'Lactose intolerant',
            'has_nut_allergy': 'Nut allergy',
        }

    def clean(self):
        cleaned = super().clean()
        # Vegan implies vegetarian
        if cleaned.get('is_vegan'):
            cleaned['is_vegetarian'] = True
        return cleaned


# ══════════════════════════════════════════════════════════════════════════════
#  FOOD INPUT
# ══════════════════════════════════════════════════════════════════════════════

class FoodInputForm(forms.Form):
    """
    Main analysis form — user picks one of three input methods.
    JS in the template shows/hides the relevant field.
    """

    INPUT_CHOICES = [
        ('image_upload', '📷 Upload a photo'),
        ('image_url',    '🔗 Paste an image URL'),
        ('text_name',    '✏️ Type the food name'),
    ]

    input_method = forms.ChoiceField(
        choices  = INPUT_CHOICES,
        initial  = 'image_upload',
        widget   = forms.RadioSelect(attrs={'class': 'ns-radio'}),
        label    = 'How would you like to identify the food?',
    )
    image = forms.ImageField(
        required = False,
        widget   = forms.ClearableFileInput(attrs={
            'class'  : 'ns-file-input',
            'accept' : 'image/*',
            'id'     : 'id_image',
        }),
        label = 'Upload image',
    )
    image_url = forms.URLField(
        required = False,
        widget   = forms.URLInput(attrs={
            'class'      : 'ns-input',
            'placeholder': 'https://example.com/food.jpg',
            'id'         : 'id_image_url',
        }),
        label = 'Image URL',
    )
    text_input = forms.CharField(
        max_length = 255,
        required   = False,
        widget     = forms.TextInput(attrs={
            'class'      : 'ns-input',
            'placeholder': 'e.g. grilled salmon, tiramisu, falafel…',
            'id'         : 'id_text_input',
        }),
        label = 'Food name',
    )
    portion_g = forms.IntegerField(
        min_value = 1,
        max_value = 2000,
        initial   = 100,
        widget    = forms.NumberInput(attrs={
            'class' : 'ns-input ns-input-sm',
            'min'   : 1,
            'max'   : 2000,
            'step'  : 10,
        }),
        label     = 'Portion size (grams)',
        help_text = 'Nutritional values will be scaled to this amount.',
    )

    def clean(self):
        cleaned = super().clean()
        method  = cleaned.get('input_method')

        if method == 'image_upload' and not cleaned.get('image'):
            self.add_error('image', 'Please upload an image.')

        elif method == 'image_url':
            url = cleaned.get('image_url', '').strip()
            if not url:
                self.add_error('image_url', 'Please paste an image URL.')

        elif method == 'text_name':
            text = cleaned.get('text_input', '').strip()
            if not text:
                self.add_error('text_input', 'Please type the food name.')

        return cleaned
