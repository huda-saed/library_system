from django import forms
from .models import BorrowRecord


class BorrowForm(forms.Form):
    """Librarian issues a book to a member (FR05)."""
    member_username = forms.CharField(
        label="Username-ka Xubinta", widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    due_days = forms.IntegerField(
        label="Dhamaadka Wakhtiga (Maalmo)", initial=14,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
