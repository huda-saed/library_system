from django.contrib import admin

from .models import Library


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'address', 'created_at')
    search_fields = ('name', 'code')
