from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(label=_('Write your password'), widget=forms.PasswordInput)
    password_repeat = forms.CharField(label=_('Repeat your password'), widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ['avatar', 'username', 'first_name', 'last_name', 'email', 'about_self']

    def password_validation(self):
        cd = self.cleaned_data
        if cd['password'] == cd['password_repeat']:
            return cd['password']
        raise forms.ValidationError(_('Password mismatch'))
    

class ConfirmationCodeForm(forms.Form):
    confirmation_code = forms.CharField(label=_('Write the confirmation code sent to your email'),
                                        min_length=6, max_length=6)


class UserEditForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['avatar', 'username', 'first_name', 'last_name', 'about_self']

    
class NewEmailForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['email']


class PasswordConfirmationForm(forms.Form):
    password = forms.CharField(label=_('Write your password'), widget=forms.PasswordInput)

class TokenAuthenticationForm(forms.Form):
    token = forms.CharField(label=_('Enter your login secret code'), min_length=50, max_length=100)