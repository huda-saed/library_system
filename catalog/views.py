from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from core.scoping import scope
from .models import Book, Category
from .forms import BookForm, CategoryForm, BookSearchForm


def staff_check(user):
    return user.is_authenticated and (user.is_admin() or user.is_librarian())


def book_list(request):
    """Public book catalog with search by title/author/ISBN/category (FR03)."""
    form = BookSearchForm(request.GET or None, user=request.user)
    books = scope(Book.objects.select_related('category'), request.user)

    if form.is_valid():
        q = form.cleaned_data.get('q')
        category = form.cleaned_data.get('category')
        if q:
            books = books.filter(
                Q(title__icontains=q) | Q(author__icontains=q) | Q(isbn__icontains=q)
            )
        if category:
            books = books.filter(category=category)
        if form.cleaned_data.get('available'):
            books = books.filter(available_copies__gt=0)

    books = books.order_by('title')
    paginator = Paginator(books, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'catalog/book_list.html', {
        'qs': params.urlencode(),
        'page_obj': page_obj,
        'form': form,
        'total_books': books.count(),
    })


def book_detail(request, pk):
    book = get_object_or_404(scope(Book.objects.select_related('category'), request.user), pk=pk)
    return render(request, 'catalog/book_detail.html', {'book': book})


@login_required
@user_passes_test(staff_check)
def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Buugga waa lagu daray liiska (Book added successfully).")
            return redirect('catalog:book_list')
    else:
        form = BookForm(initial={'available_copies': 1, 'total_copies': 1}, user=request.user)
    return render(request, 'catalog/book_form.html', {'form': form, 'action': 'Ku dar Buug Cusub'})


@login_required
@user_passes_test(staff_check)
def book_update(request, pk):
    book = get_object_or_404(scope(Book.objects.all(), request.user), pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Buugga waa la cusboonaysiiyay.")
            return redirect('catalog:book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book, user=request.user)
    return render(request, 'catalog/book_form.html', {'form': form, 'action': f'Wax ka beddel: {book.title}'})


@login_required
@user_passes_test(staff_check)
def book_delete(request, pk):
    book = get_object_or_404(scope(Book.objects.all(), request.user), pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, "Buugga waa laga saaray liiska.")
        return redirect('catalog:book_list')
    return render(request, 'catalog/book_confirm_delete.html', {'book': book})


def category_list(request):
    categories = scope(Category.objects.all(), request.user)
    return render(request, 'catalog/category_list.html', {'categories': categories})


@login_required
@user_passes_test(staff_check)
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Qaybta cusub waa la daray.")
            return redirect('catalog:category_list')
    else:
        form = CategoryForm(user=request.user)
    return render(request, 'catalog/category_form.html', {'form': form})


@login_required
@user_passes_test(staff_check)
def category_update(request, pk):
    category = get_object_or_404(scope(Category.objects.all(), request.user), pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Qaybta waa la cusboonaysiiyay.")
            return redirect('catalog:category_list')
    else:
        form = CategoryForm(instance=category, user=request.user)
    return render(request, 'catalog/category_form.html', {'form': form, 'title': f'Wax ka beddel: {category.name}'})


@login_required
@user_passes_test(staff_check)
def category_delete(request, pk):
    category = get_object_or_404(scope(Category.objects.all(), request.user), pk=pk)
    if request.method == 'POST':
        category.delete()  # books in it simply become "uncategorised"
        messages.success(request, "Qaybta waa la tirtiray.")
        return redirect('catalog:category_list')
    return render(request, 'catalog/category_confirm_delete.html', {'category': category})
