from django.contrib import admin
from .models import Book, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'library', 'description')
    list_filter = ('library',)
    search_fields = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'library', 'author', 'isbn', 'category', 'total_copies', 'available_copies', 'shelf_location')
    list_filter = ('library', 'category')
    search_fields = ('title', 'author', 'isbn')
