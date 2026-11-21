from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.core.cache import cache
from django.core.exceptions import ValidationError
from core.models import Library
from .models import User

# Basic brute-force protection for the login form (FR01 security requirement,
# report section 4.4.1). Tracks failed attempts per username in the cache.
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300  # 5 minutes


class MemberRegistrationForm(UserCreationForm):
    """Self-registration form for new library members (FR04)."""

    first_name = forms.CharField(max_length=150, required=True, label="Magaca Koowaad",
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=True, label="Magaca Labaad",
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    library = forms.ModelChoiceField(
        queryset=Library.objects.all(), required=True, label="Library", empty_label="— Dooro library —",
        widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = [
            'library', 'username', 'first_name', 'last_name', 'email', 'phone',
            'membership_type', 'password1', 'password2',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['membership_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.MEMBER
        user.library = self.cleaned_data['library']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
        return user


class LMSAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Username / Magac isticmaale",
        widget=forms.TextInput(attrs={'class': 'form-control', 'autofocus': True})
    )
    password = forms.CharField(
        label="Password / Furaha sirta ah",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    @staticmethod
    def _cache_key(username):
        return f'login_attempts:{username.strip().lower()}'

    def clean(self):
        username = self.cleaned_data.get('username') or self.data.get('username', '')
        key = self._cache_key(username) if username else None

        if key and cache.get(key, 0) >= LOGIN_MAX_ATTEMPTS:
            raise ValidationError(
                "Xisaabtan si ku meel gaar ah ayaa loo xayiray %(n)d isku day oo khalad ah ka dib. "
                "Fadlan sug %(m)d daqiiqo kadibna isku day mar kale." % {
                    'n': LOGIN_MAX_ATTEMPTS, 'm': LOGIN_LOCKOUT_SECONDS // 60,
                },
                code='rate_limited',
            )

        try:
            cleaned_data = super().clean()
        except ValidationError:
            if key:
                cache.set(key, cache.get(key, 0) + 1, LOGIN_LOCKOUT_SECONDS)
            raise
        else:
            if key:
                cache.delete(key)
            return cleaned_data


class StaffCreationForm(UserCreationForm):
    """Used by admins to create Librarian or Admin accounts."""

    class Meta:
        model = User
        fields = ['library', 'username', 'first_name', 'last_name', 'email', 'phone', 'role']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'profile_photo']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class ManagedUserForm(forms.ModelForm):
    """Used by administrators / librarians to add or edit users from the website.

    * A user who belongs to a library always creates users inside that library.
    * A librarian can only manage members; administrators (and the system owner)
      can also manage librarians and administrators.
    * On edit, leave the password fields empty to keep the current password.
    """
    password1 = forms.CharField(label="Password", required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="Ku celi password-ka", required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['library', 'username', 'first_name', 'last_name', 'email', 'phone',
                  'role', 'membership_type', 'status']

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        for name, field in self.fields.items():
            if name in ('password1', 'password2'):
                continue
            css = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css)

        self.fixed_library = actor.library if (actor is not None and actor.library_id) else None
        if self.fixed_library is not None:
            del self.fields['library']
        else:
            self.fields['library'].required = True
            self.fields['library'].empty_label = "— Dooro library —"
            self.fields['library'].queryset = Library.objects.all()

        if actor is not None and not (actor.is_superuser or actor.is_admin()):
            self.fields['role'].choices = [(User.Role.MEMBER, User.Role.MEMBER.label)]

        if not self.instance.pk:
            self.fields['password1'].required = True
            self.fields['password2'].required = True

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        if p1 or p2:
            if p1 != p2:
                self.add_error('password2', "Labada password isma mid aha.")
            elif p1:
                from django.contrib.auth.password_validation import validate_password
                try:
                    validate_password(p1, self.instance)
                except ValidationError as exc:
                    self.add_error('password1', exc)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.fixed_library is not None:
            user.library = self.fixed_library
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class LMSPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
