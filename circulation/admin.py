from django.contrib import admin
from .models import BorrowRecord, Fine, Reservation


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ('book', 'member', 'librarian', 'borrow_date', 'due_date', 'return_date', 'status')
    list_filter = ('book__library', 'status')
    search_fields = ('book__title', 'member__username')


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ('borrow_record', 'amount', 'payment_status', 'payment_date')
    list_filter = ('payment_status',)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('book', 'member', 'reservation_date', 'status')
    list_filter = ('status',)
