from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from core.scoping import scope, is_staff_user
from .forms import MemberRegistrationForm, LMSAuthenticationForm, ProfileUpdateForm, ManagedUserForm, LMSPasswordChangeForm
from .models import User


class LMSLoginView(LoginView):
    """Handles login for all roles (FR01 - User Authentication)."""
    template_name = 'accounts/login.html'
    authentication_form = LMSAuthenticationForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Demo accounts are shown only while DEBUG is on (development).
        from django.conf import settings
        context['show_demo_accounts'] = settings.DEBUG
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Ku soo dhawoow, {form.get_user().first_name or form.get_user().username}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Username ama password waa khalad. Fadlan isku day mar kale.")
        return super().form_invalid(form)


def logout_view(request):
    logout(request)
    messages.info(request, "Waad ka baxday nidaamka si guul leh (Logged out successfully).")
    return redirect('accounts:login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = MemberRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Xisaabtaada waa la abuuray! Ku soo dhawoow Library Management System.")
            return redirect('core:dashboard')
    else:
        form = MemberRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile-kaaga waa la cusboonaysiiyay.")
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


# ---------------------------------------------------------------------------
# User management (administrators and librarians)
# ---------------------------------------------------------------------------
def can_manage(actor, target):
    """Whether `actor` may edit/delete `target`."""
    if actor.is_superuser:
        return True
    if target.is_superuser or not actor.library_id or target.library_id != actor.library_id:
        return False
    if actor.is_admin():
        return True
    return actor.is_librarian() and target.role == User.Role.MEMBER


@login_required
@user_passes_test(is_staff_user)
def user_list(request):
    users = scope(User.objects.select_related('library'), request.user).order_by('role', 'username')
    q = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    if q:
        users = users.filter(Q(username__icontains=q) | Q(first_name__icontains=q)
                             | Q(last_name__icontains=q) | Q(email__icontains=q))
    if role in User.Role.values:
        users = users.filter(role=role)
    params = request.GET.copy()
    params.pop('page', None)
    page_obj = Paginator(users, 20).get_page(request.GET.get('page'))
    for u in page_obj:
        u.can_manage = can_manage(request.user, u) and u.pk != request.user.pk
    return render(request, 'accounts/user_list.html', {
        'page_obj': page_obj, 'q': q, 'role': role, 'roles': User.Role.choices, 'qs': params.urlencode(),
    })


@login_required
@user_passes_test(is_staff_user)
def user_create(request):
    initial = {'role': User.Role.MEMBER}
    form = ManagedUserForm(request.POST or None, actor=request.user, initial=initial)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Isticmaalaha cusub waa la daray.")
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'action': 'Ku Dar Isticmaale Cusub', 'creating': True})


@login_required
@user_passes_test(is_staff_user)
def user_update(request, pk):
    target = get_object_or_404(scope(User.objects.all(), request.user), pk=pk)
    if not can_manage(request.user, target):
        messages.error(request, "Ma haysatid ogolaansho aad wax uga beddesho isticmaalahan.")
        return redirect('accounts:user_list')
    form = ManagedUserForm(request.POST or None, instance=target, actor=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Isticmaalaha waa la cusboonaysiiyay.")
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'action': f'Wax ka beddel: {target.username}', 'creating': False})


@login_required
@user_passes_test(is_staff_user)
def user_delete(request, pk):
    target = get_object_or_404(scope(User.objects.all(), request.user), pk=pk)
    if target.pk == request.user.pk or not can_manage(request.user, target):
        messages.error(request, "Isticmaalahan lama tirtiri karo.")
        return redirect('accounts:user_list')
    if request.method == 'POST':
        target.delete()
        messages.success(request, "Isticmaalaha waa la tirtiray.")
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'target': target})


class LMSPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    form_class = LMSPasswordChangeForm
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        messages.success(self.request, "Password-kaaga waa la beddelay.")
        return super().form_valid(form)
