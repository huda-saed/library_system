from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from core.models import Library

User = get_user_model()


class RegistrationTests(TestCase):

    def test_self_registration_creates_member_role(self):
        library = Library.objects.create(name='Library A', code='a')
        response = self.client.post(reverse('accounts:register'), {
            'library': library.pk,
            'username': 'newmember',
            'first_name': 'Huda',
            'last_name': 'Osman',
            'email': 'huda@library-system.local',
            'phone': '',
            'membership_type': User.MembershipType.STUDENT,
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='newmember')
        self.assertEqual(user.role, User.Role.MEMBER)
        self.assertEqual(user.status, User.Status.ACTIVE)
        self.assertEqual(user.library, library)

    def test_registration_requires_library(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'nolib', 'first_name': 'A', 'last_name': 'B', 'email': 'a@b.so',
            'membership_type': User.MembershipType.STUDENT,
            'password1': 'StrongPass123!', 'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='nolib').exists())


class LoginRateLimitTests(TestCase):

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='member1', password='Member@123', role=User.Role.MEMBER,
        )

    def tearDown(self):
        cache.clear()

    def test_correct_login_succeeds(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'member1', 'password': 'Member@123',
        })
        self.assertEqual(response.status_code, 302)

    def test_account_locks_after_max_failed_attempts(self):
        from accounts.forms import LOGIN_MAX_ATTEMPTS

        for _ in range(LOGIN_MAX_ATTEMPTS):
            self.client.post(reverse('accounts:login'), {
                'username': 'member1', 'password': 'wrong-password',
            })

        # One more attempt, even with the CORRECT password, should now be blocked.
        response = self.client.post(reverse('accounts:login'), {
            'username': 'member1', 'password': 'Member@123',
        })
        self.assertEqual(response.status_code, 200)  # re-renders login form with error
        self.assertFalse(response.context['form'].is_valid())


class LoginRequiredTests(TestCase):
    """Qofka aan login gareyn ma arki karo bogagga nidaamka."""

    PROTECTED = ['core:home', 'core:about', 'core:contact', 'core:dashboard',
                 'catalog:book_list', 'catalog:category_list', 'circulation:my_loans']

    def test_anonymous_is_redirected_to_login(self):
        for name in self.PROTECTED:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)
            self.assertTrue(response.url.startswith(reverse('accounts:login')), name)

    def test_login_and_register_pages_are_public(self):
        self.assertEqual(self.client.get(reverse('accounts:login')).status_code, 200)
        self.assertEqual(self.client.get(reverse('accounts:register')).status_code, 200)

    def test_logged_in_user_can_see_pages(self):
        User.objects.create_user(username='m1', password='Member@123', role=User.Role.MEMBER)
        self.client.login(username='m1', password='Member@123')
        for name in ['core:home', 'catalog:book_list', 'core:about']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)


class ManagementTests(TestCase):
    """Adding / editing / deleting users, categories and libraries from the website."""

    def setUp(self):
        from catalog.models import Category
        self.Category = Category
        self.lib_a = Library.objects.create(name='Library A', code='a')
        self.lib_b = Library.objects.create(name='Library B', code='b')
        self.librarian = User.objects.create_user('lib_a', password='Pass@12345', role=User.Role.LIBRARIAN, library=self.lib_a)
        self.admin_a = User.objects.create_user('admin_a', password='Pass@12345', role=User.Role.ADMIN, library=self.lib_a)
        self.member_a = User.objects.create_user('mem_a', password='Pass@12345', role=User.Role.MEMBER, library=self.lib_a)
        self.member_b = User.objects.create_user('mem_b', password='Pass@12345', role=User.Role.MEMBER, library=self.lib_b)
        self.owner = User.objects.create_superuser('owner', password='Pass@12345', role=User.Role.ADMIN)

    def test_librarian_adds_member_into_own_library(self):
        self.client.login(username='lib_a', password='Pass@12345')
        r = self.client.post(reverse('accounts:user_create'), {
            'username': 'newmem', 'first_name': 'N', 'last_name': 'M', 'email': 'n@m.so',
            'role': User.Role.MEMBER, 'membership_type': User.MembershipType.STUDENT,
            'status': User.Status.ACTIVE, 'password1': 'StrongPass123!', 'password2': 'StrongPass123!',
        })
        self.assertRedirects(r, reverse('accounts:user_list'))
        self.assertEqual(User.objects.get(username='newmem').library, self.lib_a)

    def test_librarian_cannot_create_librarian(self):
        self.client.login(username='lib_a', password='Pass@12345')
        self.client.post(reverse('accounts:user_create'), {
            'username': 'sneaky', 'first_name': 'S', 'last_name': 'S', 'email': 's@s.so',
            'role': User.Role.LIBRARIAN, 'membership_type': User.MembershipType.STUDENT,
            'status': User.Status.ACTIVE, 'password1': 'StrongPass123!', 'password2': 'StrongPass123!',
        })
        self.assertFalse(User.objects.filter(username='sneaky').exists())

    def test_admin_can_create_librarian(self):
        self.client.login(username='admin_a', password='Pass@12345')
        self.client.post(reverse('accounts:user_create'), {
            'username': 'newlib', 'first_name': 'L', 'last_name': 'L', 'email': 'l@l.so',
            'role': User.Role.LIBRARIAN, 'membership_type': User.MembershipType.STAFF,
            'status': User.Status.ACTIVE, 'password1': 'StrongPass123!', 'password2': 'StrongPass123!',
        })
        self.assertEqual(User.objects.get(username='newlib').role, User.Role.LIBRARIAN)

    def test_cannot_touch_users_of_other_library(self):
        self.client.login(username='lib_a', password='Pass@12345')
        self.assertEqual(self.client.get(reverse('accounts:user_update', args=[self.member_b.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('accounts:user_delete', args=[self.member_b.pk])).status_code, 404)
        self.assertTrue(User.objects.filter(pk=self.member_b.pk).exists())

    def test_librarian_cannot_delete_admin_or_self(self):
        self.client.login(username='lib_a', password='Pass@12345')
        self.client.post(reverse('accounts:user_delete', args=[self.admin_a.pk]))
        self.client.post(reverse('accounts:user_delete', args=[self.librarian.pk]))
        self.assertTrue(User.objects.filter(pk=self.admin_a.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.librarian.pk).exists())

    def test_librarian_edits_and_deletes_member(self):
        self.client.login(username='lib_a', password='Pass@12345')
        self.client.post(reverse('accounts:user_update', args=[self.member_a.pk]), {
            'username': 'mem_a', 'first_name': 'Renamed', 'last_name': 'X', 'email': 'x@x.so',
            'role': User.Role.MEMBER, 'membership_type': User.MembershipType.STUDENT,
            'status': User.Status.SUSPENDED,
        })
        self.member_a.refresh_from_db()
        self.assertEqual(self.member_a.first_name, 'Renamed')
        self.assertEqual(self.member_a.status, User.Status.SUSPENDED)
        self.client.post(reverse('accounts:user_delete', args=[self.member_a.pk]))
        self.assertFalse(User.objects.filter(pk=self.member_a.pk).exists())

    def test_member_cannot_open_user_management(self):
        self.client.login(username='mem_a', password='Pass@12345')
        self.assertEqual(self.client.get(reverse('accounts:user_list')).status_code, 302)

    def test_user_list_shows_only_own_library(self):
        self.client.login(username='lib_a', password='Pass@12345')
        names = [u.username for u in self.client.get(reverse('accounts:user_list')).context['page_obj']]
        self.assertIn('mem_a', names)
        self.assertNotIn('mem_b', names)

    def test_category_edit_and_delete_scoped(self):
        cat_a = self.Category.objects.create(library=self.lib_a, name='Old')
        cat_b = self.Category.objects.create(library=self.lib_b, name='Other')
        self.client.login(username='lib_a', password='Pass@12345')
        self.client.post(reverse('catalog:category_update', args=[cat_a.pk]), {'name': 'New', 'description': ''})
        cat_a.refresh_from_db()
        self.assertEqual(cat_a.name, 'New')
        self.assertEqual(self.client.post(reverse('catalog:category_delete', args=[cat_b.pk])).status_code, 404)
        self.client.post(reverse('catalog:category_delete', args=[cat_a.pk]))
        self.assertFalse(self.Category.objects.filter(pk=cat_a.pk).exists())

    def test_only_superuser_manages_libraries(self):
        self.client.login(username='admin_a', password='Pass@12345')
        self.assertEqual(self.client.get(reverse('core:library_list')).status_code, 302)
        self.client.logout()
        self.client.login(username='owner', password='Pass@12345')
        r = self.client.post(reverse('core:library_create'), {'name': 'Library C', 'code': 'c', 'address': ''})
        self.assertRedirects(r, reverse('core:library_list'))
        lib_c = Library.objects.get(code='c')
        self.client.post(reverse('core:library_update', args=[lib_c.pk]), {'name': 'Library C2', 'code': 'c', 'address': 'X'})
        lib_c.refresh_from_db()
        self.assertEqual(lib_c.name, 'Library C2')
        self.client.post(reverse('core:library_delete', args=[lib_c.pk]))
        self.assertFalse(Library.objects.filter(code='c').exists())

    def test_library_with_data_cannot_be_deleted(self):
        self.client.login(username='owner', password='Pass@12345')
        self.client.post(reverse('core:library_delete', args=[self.lib_a.pk]))
        self.assertTrue(Library.objects.filter(pk=self.lib_a.pk).exists())
