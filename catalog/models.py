from django.db import models


class Category(models.Model):
    """CATEGORY Table (3.5.6) - book categories/subcategories (FR12)."""
    library = models.ForeignKey('core.Library', on_delete=models.PROTECT, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        unique_together = [('library', 'name')]

    def __str__(self):
        return self.name


class Book(models.Model):
    """BOOK Table (3.5.1) - stores details of all books (FR02)."""
    library = models.ForeignKey('core.Library', on_delete=models.PROTECT, related_name='books')
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=150)
    isbn = models.CharField("ISBN", max_length=20)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    publisher = models.CharField(max_length=150, blank=True)
    year_published = models.PositiveIntegerField(null=True, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    shelf_location = models.CharField(max_length=50, blank=True)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        unique_together = [('library', 'isbn')]

    def __str__(self):
        return f"{self.title} - {self.author}"

    @property
    def is_available(self):
        return self.available_copies > 0
