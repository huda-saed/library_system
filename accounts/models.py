from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with role-based access (FR01).

    Roles:
        ADMIN     - Full system administrator
        LIBRARIAN - Manages books, borrowing, returns, fines
        MEMBER    - Library member who borrows books
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        LIBRARIAN = 'LIBRARIAN', 'Librarian'
        MEMBER = 'MEMBER', 'Member'

    library = models.ForeignKey(
        'core.Library', on_delete=models.PROTECT, null=True, blank=True, related_name='users',
        help_text="The library this user belongs to. Leave empty only for the system owner (superuser).",
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    phone = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)

    class MembershipType(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        STAFF = 'STAFF', 'Staff'
        PUBLIC = 'PUBLIC', 'Public'

    membership_type = models.CharField(
        max_length=10, choices=MembershipType.choices, default=MembershipType.STUDENT
    )

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        EXPIRED = 'EXPIRED', 'Expired'

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    registration_date = models.DateField(auto_now_add=True)

    def is_admin(self):
        return self.role == self.Role.ADMIN

    def is_librarian(self):
        return self.role == self.Role.LIBRARIAN

    def is_member(self):
        return self.role == self.Role.MEMBER

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
