from django import forms
from django.contrib.auth.forms import UserCreationForm

from apps.utils import delete_replaced_file, validate_image_size

from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    # keep username field settings
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email']

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email


class ProfileForm(forms.ModelForm):
    remove_avatar = forms.BooleanField(required=False, label='Remove current avatar')

    class Meta:
        model = User
        fields = ['avatar', 'email', 'bio']
        widgets = {
            'avatar': forms.FileInput(attrs={'accept': 'image/*'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell others about yourself'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.old_avatar_name = self.instance.avatar.name

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        other_users = User.objects.exclude(id=self.instance.id)
        if other_users.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        return validate_image_size(avatar, max_mb=2)

    def save(self, commit=True):
        user = super().save(commit=False)

        new_avatar_uploaded = 'avatar' in self.changed_data
        if self.cleaned_data.get('remove_avatar') and not new_avatar_uploaded:
            user.avatar = ''

        if commit:
            user.save()
            delete_replaced_file(self.old_avatar_name, user.avatar.name)
        return user

