from django.test import TestCase

from core.models import Library
from .models import Book, Category


class CatalogModelTests(TestCase):

    def setUp(self):
        self.library = Library.objects.create(name='Library A', code='a')
        self.category = Category.objects.create(library=self.library, name='Science')

    def test_book_is_available_when_copies_left(self):
        book = Book.objects.create(
            library=self.library,
            title='Cosmos', author='Carl Sagan', isbn='9780345539434',
            category=self.category, total_copies=2, available_copies=2,
        )
        self.assertTrue(book.is_available)

    def test_book_not_available_when_no_copies_left(self):
        book = Book.objects.create(
            library=self.library,
            title='Cosmos', author='Carl Sagan', isbn='9780345539434',
            category=self.category, total_copies=1, available_copies=0,
        )
        self.assertFalse(book.is_available)

    def test_same_isbn_allowed_in_another_library(self):
        other = Library.objects.create(name='Library B', code='b')
        other_cat = Category.objects.create(library=other, name='Science')
        for lib, cat in ((self.library, self.category), (other, other_cat)):
            Book.objects.create(library=lib, title='T', author='A', isbn='SAME-ISBN', category=cat)
        self.assertEqual(Book.objects.filter(isbn='SAME-ISBN').count(), 2)

    def test_isbn_must_be_unique(self):
        Book.objects.create(
            library=self.library,
            title='Book A', author='Author A', isbn='DUPLICATE-1',
            category=self.category, total_copies=1, available_copies=1,
        )
        with self.assertRaises(Exception):
            Book.objects.create(
            library=self.library,
                title='Book B', author='Author B', isbn='DUPLICATE-1',
                category=self.category, total_copies=1, available_copies=1,
            )
