from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, ProtectedError
from django.shortcuts import render, redirect, get_object_or_404

from catalog.models import Book, Category
from core.forms import LibraryForm
from core.models import Library
from core.scoping import scope
from circulation.models import BorrowRecord, Fine, Reservation


def home(request):
    """Public landing page with hero carousel (FR - general UI)."""
    books = scope(Book.objects.all(), request.user)
    all_categories = scope(Category.objects.all(), request.user)
    latest_books = books.select_related('category').order_by('-date_added')[:6]
    categories = all_categories[:6]
    context = {
        'latest_books': latest_books,
        'categories': categories,
        'total_books': books.count(),
        'total_categories': all_categories.count(),
    }
    return render(request, 'core/home.html', context)


def about(request):
    return render(request, 'core/about.html')


def contact(request):
    return render(request, 'core/contact.html')


@login_required
def dashboard(request):
    """Role-based dashboard landing after login."""
    user = request.user
    context = {'user': user}

    if user.is_admin() or user.is_librarian():
        context.update({
            'total_books': scope(Book.objects.all(), user).count(),
            'total_members': scope(user.__class__.objects.filter(role='MEMBER'), user).count(),
            'active_loans': scope(BorrowRecord.objects.filter(status__in=['BORROWED', 'OVERDUE']), user, 'book__library').count(),
            'overdue_loans': scope(BorrowRecord.objects.filter(status='OVERDUE'), user, 'book__library').count(),
            'unpaid_fines': scope(Fine.objects.filter(payment_status='UNPAID'), user, 'borrow_record__book__library').count(),
            'pending_reservations': scope(Reservation.objects.filter(status='PENDING'), user, 'book__library').count(),
        })
        return render(request, 'core/dashboard_staff.html', context)
    else:
        context.update({
            'my_active_loans': BorrowRecord.objects.filter(member=user, status__in=['BORROWED', 'OVERDUE']).count(),
            'my_fines': Fine.objects.filter(borrow_record__member=user, payment_status='UNPAID').count(),
            'my_reservations': Reservation.objects.filter(member=user, status='PENDING').count(),
        })
        return render(request, 'core/dashboard_member.html', context)


# ---------------------------------------------------------------------------
# Library management (system owner / superuser only)
# ---------------------------------------------------------------------------
superuser_required = user_passes_test(lambda u: u.is_authenticated and u.is_superuser)


@login_required
@superuser_required
def library_list(request):
    libraries = Library.objects.annotate(
        book_count=Count('books', distinct=True),
        user_count=Count('users', distinct=True),
    )
    return render(request, 'core/library_list.html', {'libraries': libraries})


@login_required
@superuser_required
def library_create(request):
    form = LibraryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Library cusub waa la daray.")
        return redirect('core:library_list')
    return render(request, 'core/library_form.html', {'form': form, 'action': 'Ku Dar Library Cusub'})


@login_required
@superuser_required
def library_update(request, pk):
    library = get_object_or_404(Library, pk=pk)
    form = LibraryForm(request.POST or None, instance=library)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Library-ga waa la cusboonaysiiyay.")
        return redirect('core:library_list')
    return render(request, 'core/library_form.html', {'form': form, 'action': f'Wax ka beddel: {library.name}'})


@login_required
@superuser_required
def library_delete(request, pk):
    library = get_object_or_404(Library, pk=pk)
    if request.method == 'POST':
        try:
            library.delete()
            messages.success(request, "Library-ga waa la tirtiray.")
        except ProtectedError:
            messages.error(request, "Library-gan lama tirtiri karo: wuxuu leeyahay buugaag, qaybo ama isticmaalayaal. "
                                    "Marka hore tirtir ama u wareeji.")
        return redirect('core:library_list')
    return render(request, 'core/library_confirm_delete.html', {'library': library})
