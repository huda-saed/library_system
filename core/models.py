from django.db import models


class Library(models.Model):
    """A single library. Every user, category and book belongs to exactly one
    library so that several libraries can share one system without their data
    getting mixed together."""
    name = models.CharField(max_length=150, unique=True)
    code = models.SlugField(max_length=50, unique=True,
                            help_text="Short unique code, e.g. 'main' or 'branch-2'.")
    address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Libraries"
        ordering = ['name']

    def __str__(self):
        return self.name
