from django import forms

from .models import Library


class LibraryForm(forms.ModelForm):
    class Meta:
        model = Library
        fields = ['name', 'code', 'address']
        labels = {'name': 'Magaca Library-ga', 'code': 'Code (gaaban, tusaale: main)', 'address': 'Cinwaanka'}
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
        }
