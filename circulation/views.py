from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Count, Q
import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from catalog.models import Book
from core.scoping import scope
from .models import BorrowRecord, Fine, Reservation
from .forms import BorrowForm

User = get_user_model()

# Maximum number of books a member may have on loan at the same time (FR05 rule,
# described in the project report section 4.4.4).
MAX_ACTIVE_LOANS = 3
MAX_RENEWALS = 2      # how many times one loan can be extended
RENEW_DAYS = 7        # days added by each renewal


def staff_check(user):
    return user.is_authenticated and (user.is_admin() or user.is_librarian())


def _notify(email, subject, message):
    """Best-effort email notification (uses console backend in dev by default)."""
    if not email:
        return
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)
    except Exception:
        # Notifications must never break the borrow/return flow.
        pass


def _sync_overdue_status():
    """Mark any borrowed records past their due date as OVERDUE (FR06)."""
    today = timezone.localdate()
    BorrowRecord.objects.filter(
        status=BorrowRecord.Status.BORROWED, due_date__lt=today
    ).update(status=BorrowRecord.Status.OVERDUE)


@login_required
@user_passes_test(staff_check)
def borrow_book(request, book_id):
    """Librarian issues a book to a member (FR05)."""
    book = get_object_or_404(scope(Book.objects.all(), request.user), pk=book_id)

    if request.method == 'POST':
        form = BorrowForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['member_username']
            due_days = form.cleaned_data['due_days']
            try:
                member = User.objects.get(username=username, role=User.Role.MEMBER, library=book.library)
            except User.DoesNotExist:
                messages.error(request, "Xubinta lama helin. Fadlan hubi username-ka.")
                return render(request, 'circulation/borrow_form.html', {'form': form, 'book': book})

            if member.status != User.Status.ACTIVE:
                messages.error(request, f"Xubinta '{member}' xaaladeeda ma ahan Active ({member.get_status_display()}).")
                return redirect('catalog:book_detail', pk=book.pk)

            # FR05 rule: a member cannot exceed the configured borrowing limit.
            active_loans_count = BorrowRecord.objects.filter(
                member=member, status__in=[BorrowRecord.Status.BORROWED, BorrowRecord.Status.OVERDUE]
            ).count()
            if active_loans_count >= MAX_ACTIVE_LOANS:
                messages.error(
                    request,
                    f"'{member}' waxay hore u haysaa {active_loans_count} buug oo aan weli soo celin. "
                    f"Xadka ugu badan ee la amaahin karo hal mar waa {MAX_ACTIVE_LOANS} buug."
                )
                return redirect('catalog:book_detail', pk=book.pk)

            # Lock the book row for the duration of the check-and-update so two
            # librarians cannot both issue the last available copy at once.
            with transaction.atomic():
                locked_book = Book.objects.select_for_update().get(pk=book.pk)
                if locked_book.available_copies < 1:
                    messages.error(request, "Buugan hadda ma haysto nuqul la heli karo.")
                    return redirect('catalog:book_detail', pk=book.pk)

                record = BorrowRecord.objects.create(
                    member=member,
                    book=locked_book,
                    librarian=request.user,
                    due_date=timezone.localdate() + timedelta(days=due_days),
                )
                locked_book.available_copies -= 1
                locked_book.save()

            _notify(
                member.email,
                "Xaqiijinta Amaahda Buug - Library System",
                (
                    f"Salaan {member.first_name or member.username},\n\n"
                    f"Waxaad amaahatay buugga '{book.title}'.\n"
                    f"Taariikhda dib-u-celinta waa: {record.due_date}.\n\n"
                    "Mahadsanid,\nLibrary System"
                ),
            )

            messages.success(request, f"'{book.title}' waxaa la siiyay {member}.")
            return redirect('catalog:book_detail', pk=book.pk)
    else:
        form = BorrowForm(initial={'due_days': settings.LOAN_PERIOD_DAYS})

    return render(request, 'circulation/borrow_form.html', {'form': form, 'book': book})


@login_required
@user_passes_test(staff_check)
def return_book(request, record_id):
    """Process a book return, update availability, calculate fine (FR06, FR07)."""
    record = get_object_or_404(scope(BorrowRecord.objects.all(), request.user, 'book__library'), pk=record_id)

    if record.status == BorrowRecord.Status.RETURNED:
        messages.warning(request, "Buugan mar hore waa la soo celiyay.")
        return redirect('circulation:reports')

    record.return_date = timezone.localdate()
    overdue_days = max(0, (record.return_date - record.due_date).days)
    record.status = BorrowRecord.Status.RETURNED
    record.save()

    record.book.available_copies += 1
    record.book.save()

    if overdue_days > 0:
        fine_amount = overdue_days * settings.FINE_DAILY_RATE
        Fine.objects.update_or_create(
            borrow_record=record,
            defaults={'amount': fine_amount, 'payment_status': Fine.PaymentStatus.UNPAID},
        )
        messages.warning(
            request,
            f"Buugga waa la soo celiyay {overdue_days} maalmood oo dib u dhac ah. "
            f"Ganaax lacageed: {fine_amount}."
        )
        _notify(
            record.member.email,
            "Ogeysiin Ganaax - Library System",
            (
                f"Salaan {record.member.first_name or record.member.username},\n\n"
                f"Buugga '{record.book.title}' waxaad soo celisay {overdue_days} maalmood oo dib u dhac ah.\n"
                f"Qadarka ganaaxa: {fine_amount}. Fadlan booqo profile-kaaga si aad u aragto.\n\n"
                "Mahadsanid,\nLibrary System"
            ),
        )
    else:
        messages.success(request, "Buugga waa la soo celiyay wakhtigiisii, mahadsanid!")

    # Tell the first member waiting for this book that it is available again.
    waiting = Reservation.objects.filter(book=record.book, status=Reservation.Status.PENDING) \
        .order_by('reservation_date').select_related('member').first()
    if waiting:
        _notify(
            waiting.member.email,
            "Buuggaagii aad dalbatay waa diyaar - Library System",
            f"Salaan {waiting.member.first_name or waiting.member.username},\n\n"
            f"Buugga '{record.book.title}' hadda waa la heli karaa. Fadlan la xiriir librarian-ka.\n\n"
            "Mahadsanid,\nLibrary System",
        )
        messages.info(request, f"Xubinta sugaysa buugan ({waiting.member}) waa la ogeysiiyay.")

    return redirect('circulation:reports')


@login_required
def my_loans(request):
    """Member's own borrowing history + active loans."""
    _sync_overdue_status()
    records = BorrowRecord.objects.filter(member=request.user).select_related('book')
    return render(request, 'circulation/my_loans.html', {'records': records})


@login_required
def my_fines(request):
    """Fines belonging to the logged-in member (FR08)."""
    fines = Fine.objects.filter(borrow_record__member=request.user).select_related('borrow_record__book')
    return render(request, 'circulation/fines.html', {'fines': fines})


@login_required
def reserve_book(request, book_id):
    """Member reserves a book currently on loan (FR09)."""
    book = get_object_or_404(scope(Book.objects.all(), request.user), pk=book_id)
    if request.method == 'POST':
        if book.available_copies > 0:
            messages.info(request, "Buugan hadda wuu heli karaa — kama baahnid inaad dalbato reservation.")
        else:
            Reservation.objects.get_or_create(member=request.user, book=book, status=Reservation.Status.PENDING)
            messages.success(request, f"Waxaad dalbatay '{book.title}'. Waan kuu ogeysiin doonaa marka la heli karo.")
        return redirect('catalog:book_detail', pk=book.pk)
    return redirect('catalog:book_detail', pk=book.pk)


@login_required
def my_reservations(request):
    reservations = Reservation.objects.filter(member=request.user).select_related('book')
    return render(request, 'circulation/reservations.html', {'reservations': reservations})


@login_required
@user_passes_test(staff_check)
def reports(request):
    """Librarian/Admin reports dashboard (FR10)."""
    _sync_overdue_status()

    user = request.user
    active_loans = scope(BorrowRecord.objects.filter(
        status__in=[BorrowRecord.Status.BORROWED, BorrowRecord.Status.OVERDUE]
    ), user, 'book__library').select_related('book', 'member')
    overdue_loans = active_loans.filter(status=BorrowRecord.Status.OVERDUE)
    unpaid_fines = scope(Fine.objects.filter(payment_status=Fine.PaymentStatus.UNPAID), user,
                         'borrow_record__book__library').select_related('borrow_record')
    pending_reservations = scope(Reservation.objects.filter(status=Reservation.Status.PENDING), user,
                                 'book__library').select_related('book', 'member')

    stats = {
        'total_books': scope(Book.objects.all(), user).count(),
        'total_members': scope(User.objects.filter(role=User.Role.MEMBER), user).count(),
        'active_loans_count': active_loans.count(),
        'overdue_count': overdue_loans.count(),
        'unpaid_fines_total': sum(f.amount for f in unpaid_fines) if unpaid_fines else 0,
    }

    return render(request, 'circulation/reports.html', {
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'unpaid_fines': unpaid_fines,
        'pending_reservations': pending_reservations,
        'stats': stats,
    })


@login_required
@user_passes_test(staff_check)
def mark_fine_paid(request, fine_id):
    fine = get_object_or_404(scope(Fine.objects.all(), request.user, 'borrow_record__book__library'), pk=fine_id)
    fine.payment_status = Fine.PaymentStatus.PAID
    fine.payment_date = timezone.localdate()
    fine.save()
    messages.success(request, "Ganaaxa waa la calaamadeeyay in la bixiyay.")
    return redirect('circulation:reports')


# ---------------------------------------------------------------------------
# Loan history, renewals, reservation cancel, CSV export
# ---------------------------------------------------------------------------
@login_required
@user_passes_test(staff_check)
def loan_list(request):
    """All loans of the library (active and returned) with search and filter."""
    _sync_overdue_status()
    records = scope(BorrowRecord.objects.select_related('book', 'member'), request.user, 'book__library')
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if q:
        records = records.filter(
            Q(book__title__icontains=q) | Q(book__isbn__icontains=q) | Q(member__username__icontains=q)
            | Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q)
        )
    if status in BorrowRecord.Status.values:
        records = records.filter(status=status)
    params = request.GET.copy()
    params.pop('page', None)
    page_obj = Paginator(records, 20).get_page(request.GET.get('page'))
    return render(request, 'circulation/loan_list.html', {
        'page_obj': page_obj, 'q': q, 'status': status,
        'statuses': BorrowRecord.Status.choices, 'qs': params.urlencode(),
        'max_renewals': MAX_RENEWALS,
    })


@login_required
def renew_loan(request, record_id):
    """Extend a loan by RENEW_DAYS (member for own loans, staff for their library)."""
    if request.method != 'POST':
        return redirect('circulation:my_loans')
    if staff_check(request.user):
        record = get_object_or_404(scope(BorrowRecord.objects.all(), request.user, 'book__library'), pk=record_id)
    else:
        record = get_object_or_404(BorrowRecord, pk=record_id, member=request.user)
    _sync_overdue_status()
    record.refresh_from_db()

    if record.status == BorrowRecord.Status.RETURNED:
        messages.warning(request, "Buugan mar hore waa la soo celiyay.")
    elif record.is_overdue:
        messages.error(request, "Amaah dib u dhacday lama cusboonaysiin karo. Fadlan soo celi buugga.")
    elif record.renewal_count >= MAX_RENEWALS:
        messages.error(request, f"Amaahda waa la cusboonaysiin karaa ugu badnaan {MAX_RENEWALS} jeer.")
    elif Reservation.objects.filter(book=record.book, status=Reservation.Status.PENDING).exclude(member=record.member).exists():
        messages.error(request, "Cusboonaysiin lama sameyn karo: xubin kale ayaa buuggan dalbatay.")
    else:
        record.due_date += timedelta(days=RENEW_DAYS)
        record.renewal_count += 1
        record.save()
        messages.success(request, f"Amaahda waa la kordhiyay {RENEW_DAYS} maalmood. Dhamaadka cusub: {record.due_date}.")
    return redirect('circulation:loan_list' if staff_check(request.user) else 'circulation:my_loans')


@login_required
def cancel_reservation(request, reservation_id):
    if request.method != 'POST':
        return redirect('circulation:my_reservations')
    if staff_check(request.user):
        reservation = get_object_or_404(scope(Reservation.objects.all(), request.user, 'book__library'), pk=reservation_id)
    else:
        reservation = get_object_or_404(Reservation, pk=reservation_id, member=request.user)
    if reservation.status == Reservation.Status.PENDING:
        reservation.status = Reservation.Status.CANCELLED
        reservation.save()
        messages.success(request, "Dalabka waa la joojiyay.")
    return redirect('circulation:reports' if staff_check(request.user) else 'circulation:my_reservations')


def _csv_response(filename):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')  # so Excel opens Somali characters correctly
    return response


@login_required
@user_passes_test(staff_check)
def export_books_csv(request):
    response = _csv_response('books.csv')
    writer = csv.writer(response)
    writer.writerow(['Library', 'Title', 'Author', 'ISBN', 'Category', 'Publisher', 'Year', 'Total copies', 'Available copies'])
    for b in scope(Book.objects.select_related('category', 'library'), request.user).order_by('library__name', 'title'):
        writer.writerow([b.library.name, b.title, b.author, b.isbn, b.category.name if b.category else '',
                         b.publisher, b.year_published or '', b.total_copies, b.available_copies])
    return response


@login_required
@user_passes_test(staff_check)
def export_loans_csv(request):
    response = _csv_response('loans.csv')
    writer = csv.writer(response)
    writer.writerow(['Library', 'Book', 'ISBN', 'Member', 'Borrowed', 'Due', 'Returned', 'Status', 'Renewals'])
    records = scope(BorrowRecord.objects.select_related('book__library', 'member'), request.user, 'book__library')
    for r in records:
        writer.writerow([r.book.library.name, r.book.title, r.book.isbn, r.member.username, r.borrow_date,
                         r.due_date, r.return_date or '', r.status, r.renewal_count])
    return response
