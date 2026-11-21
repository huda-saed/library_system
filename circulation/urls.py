from django.urls import path
from . import views

app_name = 'circulation'

urlpatterns = [
    path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('return/<int:record_id>/', views.return_book, name='return_book'),
    path('my-loans/', views.my_loans, name='my_loans'),
    path('my-fines/', views.my_fines, name='my_fines'),
    path('reserve/<int:book_id>/', views.reserve_book, name='reserve_book'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('reports/', views.reports, name='reports'),
    path('loans/', views.loan_list, name='loan_list'),
    path('renew/<int:record_id>/', views.renew_loan, name='renew_loan'),
    path('reservation/<int:reservation_id>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    path('export/books.csv', views.export_books_csv, name='export_books'),
    path('export/loans.csv', views.export_loans_csv, name='export_loans'),
    path('fine/<int:fine_id>/paid/', views.mark_fine_paid, name='mark_fine_paid'),
]
