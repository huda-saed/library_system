from django.conf import settings
from django.db import models
from django.utils import timezone

from catalog.models import Book


class BorrowRecord(models.Model):
    """BORROW_RECORD Table (3.5.4) - every borrowing/return transaction (FR05, FR06)."""

    class Status(models.TextChoices):
        BORROWED = 'BORROWED', 'Borrowed'
        RETURNED = 'RETURNED', 'Returned'
        OVERDUE = 'OVERDUE', 'Overdue'

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='borrow_records'
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_records')
    librarian = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='issued_records'
    )
    borrow_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.BORROWED)
    renewal_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['-borrow_date']

    def __str__(self):
        return f"{self.book.title} -> {self.member} ({self.status})"

    @property
    def is_overdue(self):
        if self.status == self.Status.RETURNED:
            return False
        return timezone.localdate() > self.due_date

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        return (timezone.localdate() - self.due_date).days


class Fine(models.Model):
    """FINE Table (3.5.5) - overdue fines (FR07, FR08)."""

    class PaymentStatus(models.TextChoices):
        UNPAID = 'UNPAID', 'Unpaid'
        PAID = 'PAID', 'Paid'

    borrow_record = models.OneToOneField(BorrowRecord, on_delete=models.CASCADE, related_name='fine')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    payment_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Fine {self.amount} for {self.borrow_record} ({self.payment_status})"


class Reservation(models.Model):
    """RESERVATION Table (3.5.7) - hold requests for on-loan books (FR09)."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        FULFILLED = 'FULFILLED', 'Fulfilled'
        CANCELLED = 'CANCELLED', 'Cancelled'

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations'
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ['-reservation_date']

    def __str__(self):
        return f"{self.member} reserved {self.book.title} ({self.status})"
