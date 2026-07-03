# music/forms.py
from django import forms
from .models import Song, CustomUser, Comment
from django.contrib.auth.forms import UserCreationForm
from django import forms

# East African Countries
COUNTRY_CHOICES = [
    ('uganda', '🇺🇬 Uganda'),
    ('kenya', '🇰🇪 Kenya'),
    ('tanzania', '🇹🇿 Tanzania'),
    ('rwanda', '🇷🇼 Rwanda'),
    ('burundi', '🇧🇮 Burundi'),
    ('south_sudan', '🇸🇸 South Sudan'),
    ('other', '🌍 Other'),
]
# ============================================================
# USER SIGNUP FORM (Regular listeners)
# ============================================================
class UserSignupForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control bg-dark text-white border-secondary',
        'placeholder': 'your@email.com'
    }))
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'Confirm password'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'user'
        user.is_artist = False
        if commit:
            user.save()
        return user


# ============================================================
# ARTIST SIGNUP FORM (Musicians/Content creators)
# ============================================================
class ArtistSignupForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control bg-dark text-white border-secondary',
        'placeholder': 'your@email.com'
    }))
    whatsapp_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control bg-dark text-white border-secondary',
        'placeholder': 'WhatsApp number (for merch sales)'
    }))
    display_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control bg-dark text-white border-secondary',
        'placeholder': 'Stage name / Display name (spaces allowed)'
    }), help_text="Your stage name. Leave blank to use your username.")
    
    # 🆕 ADD COUNTRY FIELD
    country = forms.ChoiceField(choices=COUNTRY_CHOICES, required=True, widget=forms.Select(attrs={
        'class': 'form-control bg-dark text-white border-secondary'
    }))
    
    # 🆕 ADD CITY FIELD (Optional)
    city = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control bg-dark text-white border-secondary',
        'placeholder': 'e.g., Kampala, Nairobi, Dar es Salaam'
    }))
    
    class Meta:
        model = CustomUser
        fields = ['username', 'display_name', 'email', 'password1', 'password2', 'whatsapp_number', 'country', 'city']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'Username (no spaces, for login)'
        })
        self.fields['username'].help_text = 'Required. Letters, digits and @/./+/-/_ only. No spaces.'
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'Confirm password'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'artist'
        user.is_artist = True
        
        # Set display_name if provided
        display_name = self.cleaned_data.get('display_name')
        if display_name:
            user.display_name = display_name
        
        # 🆕 Set country and city
        user.country = self.cleaned_data.get('country')
        user.city = self.cleaned_data.get('city')
        
        if commit:
            user.save()
        return user


# ============================================================
# SONG FORM
# ============================================================
class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ['title', 'genre', 'cover_image', 'audio_file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'placeholder': 'Song title'
            }),
            'genre': forms.Select(attrs={
                'class': 'form-select bg-dark text-white border-secondary'
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary'
            }),
            'audio_file': forms.FileInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary'
            }),
        }


# ============================================================
# COMMENT FORM
# ============================================================
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'rows': 2,
                'placeholder': 'Write a comment... (+5 points)'
            })
        }


# ============================================================
# LOGIN FORM (Custom styling)
# ============================================================
from django.contrib.auth.forms import AuthenticationForm

class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'Username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'Password'
        })
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['display_name', 'bio', 'location', 'website', 'profile_picture', 'whatsapp_number']
        widgets = {
            'display_name': forms.TextInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'placeholder': 'Your stage name (spaces allowed)'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control bg-dark text-white border-secondary', 
                'rows': 4,
                'placeholder': 'Tell your fans about yourself...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'placeholder': 'e.g., Kampala, Uganda'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary', 
                'placeholder': 'https://yourwebsite.com'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'accept': 'image/*'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary', 
                'placeholder': '0712 345 678'
            }),
        }
        labels = {
            'display_name': 'Display Name / Stage Name',
            'bio': 'Biography',
            'location': 'Location',
            'website': 'Website',
            'profile_picture': 'Profile Picture',
            'whatsapp_number': 'WhatsApp Number',
        }
        help_texts = {
            'display_name': 'This name will appear publicly. Spaces are allowed!',
            'bio': 'Tell your fans about yourself and your music',
            'website': 'Your official website or social media link',
            'profile_picture': 'Upload a profile picture (JPG, PNG)',
            'whatsapp_number': 'Fans can contact you for bookings and merch',
        }
    
    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website and not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        return website
    
    def clean_whatsapp_number(self):
        whatsapp = self.cleaned_data.get('whatsapp_number')
        if whatsapp:
            # Remove any spaces or special characters
            import re
            whatsapp = re.sub(r'[\s\-\(\)\+]', '', whatsapp)
            if len(whatsapp) < 10:
                raise forms.ValidationError('Please enter a valid phone number')
        return whatsapp
class AdvertiserRequestForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['wants_to_advertise', 'advertiser_business_name', 'advertiser_message']
        widgets = {
            'wants_to_advertise': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'advertiser_business_name': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'Your business/company name'}),
            'advertiser_message': forms.Textarea(attrs={'class': 'form-control bg-dark text-white border-secondary', 'rows': 4, 'placeholder': 'Tell us about your advertising needs...'}),
        }        