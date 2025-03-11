from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

from .models import Feedback

User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username')


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['feedback_message', 'feedback_name', 'feedback_email']



from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=False, label='Номер телефона')
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput,
        help_text='Ваш пароль должен содержать как минимум 8 символов.'
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput,
        help_text='Введите тот же пароль еще раз для подтверждения.'
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'phone_number', 'password1', 'password2')
        labels = {
            'username': 'Логин',
            'phone_number': 'Номер телефона',
        }

    def clean(self):
        cleaned_data = super().clean()
        phone_number = cleaned_data.get('phone_number')

        if not phone_number:
            raise forms.ValidationError('Необходимо указать телефонный номер.')
        return cleaned_data

from django import forms
import phonenumbers

class PhoneNumberForm(forms.Form):
    phone_number = forms.CharField(max_length=15)

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        try:
            parsed_number = phonenumbers.parse(phone_number, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise forms.ValidationError("Invalid phone number")
        except phonenumbers.phonenumberutil.NumberParseException:
            raise forms.ValidationError("Invalid phone number format")
        return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)