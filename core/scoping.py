"""Helpers that keep every library's data separate.

A user who belongs to a library only ever sees that library's data. A
superuser with no library assigned (the system owner) sees all libraries.
"""


def scope(queryset, user, field='library'):
    """Limit `queryset` to the library of `user`.

    `field` is the lookup path to the library, e.g. 'library' for Book,
    'book__library' for BorrowRecord, 'borrow_record__book__library' for Fine.
    """
    if user.library_id:
        return queryset.filter(**{field: user.library_id})
    if user.is_superuser:
        return queryset
    return queryset.none()


def is_staff_user(user):
    """Administrator or librarian (or the system owner)."""
    return user.is_authenticated and (user.is_superuser or user.is_admin() or user.is_librarian())
