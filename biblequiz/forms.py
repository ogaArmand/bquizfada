from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.contrib.auth.models import User

# Formulaire
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['date_of_birth', 'phone_number']

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    show_passwords = forms.BooleanField(label="Afficher les mots de passe", required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name',)  # Ajoutez d'autres champs si nécessaire
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Login'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Adresse email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control','placeholder': 'Mot de passe'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmer le mot de passe'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = "Votre mot de passe ne peut pas être trop similaire à vos autres informations personnelles. Votre mot de passe doit contenir au moins 8 caractères. Votre mot de passe ne peut pas être un mot de passe couramment utilisé. Votre mot de passe ne peut pas être entièrement numérique."
        self.fields['password2'].help_text = "Entrez le même mot de passe qu'auparavant, pour vérification."

    class Media:
        js = ('js/show_passwords.js',)
