from django import forms
from core.scoping import scope
from .models import Book, Category


class LibraryScopedForm(forms.ModelForm):
    """Ties a form to the library of the logged-in user.

    Users that belong to a library never see a 'library' field: their library is
    applied automatically. A system owner (superuser without a library) picks it.
    """
    unique_in_library = None  # field name that must be unique inside a library

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fixed_library = user.library if (user is not None and user.library_id) else None
        if self.fixed_library is not None:
            del self.fields['library']
        else:
            self.fields['library'].widget.attrs.update({'class': 'form-select'})
        self.limit_choices()

    def limit_choices(self):
        pass

    def _library(self):
        return self.fixed_library or self.cleaned_data.get('library')

    def clean(self):
        cleaned = super().clean()
        library = self._library()
        field = self.unique_in_library
        if library and field and cleaned.get(field):
            duplicates = self._meta.model.objects.filter(library=library, **{field: cleaned[field]})
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                self.add_error(field, "Hore ayaa loogu diiwaangeliyay library-gan (already exists in this library).")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.fixed_library is not None:
            obj.library = self.fixed_library
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class BookForm(LibraryScopedForm):
    unique_in_library = 'isbn'

    def limit_choices(self):
        if self.fixed_library is not None:
            self.fields['category'].queryset = Category.objects.filter(library=self.fixed_library)

    def clean(self):
        cleaned = super().clean()
        category, library = cleaned.get('category'), self._library()
        if category and library and category.library_id != library.pk:
            self.add_error('category', "Qaybtan ma ka tirsana library-gan (category belongs to another library).")
        return cleaned

    class Meta:
        model = Book
        fields = [
            'library', 'title', 'author', 'isbn', 'category', 'publisher',
            'year_published', 'total_copies', 'available_copies',
            'shelf_location', 'cover_image',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control'}),
            'year_published': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-control'}),
            'shelf_location': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CategoryForm(LibraryScopedForm):
    unique_in_library = 'name'

    class Meta:
        model = Category
        fields = ['library', 'name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BookSearchForm(forms.Form):
    q = forms.CharField(required=False, label='', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Raadi buug: cinwaan, qoraa, ISBN...'}))
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), required=False, label='',
        widget=forms.Select(attrs={'class': 'form-select'}))
    available = forms.BooleanField(
        required=False, label='Kuwa la heli karo kaliya',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = 'Dhammaan qaybaha'
        if user is not None:
            self.fields['category'].queryset = scope(Category.objects.all(), user)
