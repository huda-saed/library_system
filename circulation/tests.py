from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Book, Category
from core.models import Library
from .models import BorrowRecord, Fine, Reservation

User = get_user_model()


class CirculationTestCase(TestCase):
    """Covers the functional requirements described in Chapter 2 & 4 of the
    project report: borrowing, returning, fine calculation, the borrowing
    limit, and availability tracking."""

    def setUp(self):
        self.library = Library.objects.create(name='Library A', code='a')
        self.librarian = User.objects.create_user(
            username='librarian1', password='Librarian@123',
            role=User.Role.LIBRARIAN, is_staff=True, library=self.library,
        )
        self.member = User.objects.create_user(
            username='member1', password='Member@123', email='member1@library-system.local',
            role=User.Role.MEMBER, library=self.library,
        )
        self.category = Category.objects.create(library=self.library, name='Fiction')
        self.book = Book.objects.create(
            library=self.library, title='Test Book', author='Test Author', isbn='1111111111',
            category=self.category, total_copies=1, available_copies=1,
        )
        self.client.login(username='librarian1', password='Librarian@123')

    def _borrow(self, book, due_days=14):
        return self.client.post(
            reverse('circulation:borrow_book', args=[book.pk]),
            {'member_username': self.member.username, 'due_days': due_days},
        )

    def test_borrow_decrements_available_copies(self):
        self._borrow(self.book)
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 0)
        self.assertEqual(BorrowRecord.objects.filter(member=self.member).count(), 1)

    def test_cannot_borrow_when_no_copies_available(self):
        self.book.available_copies = 0
        self.book.save()
        self._borrow(self.book)
        self.assertEqual(BorrowRecord.objects.filter(member=self.member).count(), 0)

    def test_borrowing_limit_enforced(self):
        """A member cannot have more than MAX_ACTIVE_LOANS active loans (FR05)."""
        for i in range(3):
            b = Book.objects.create(
                library=self.library, title=f'Book {i}', author='Author', isbn=f'ISBN-{i}',
                category=self.category, total_copies=1, available_copies=1,
            )
            self._borrow(b)
        self.assertEqual(
            BorrowRecord.objects.filter(member=self.member, status='BORROWED').count(), 3
        )

        # A 4th book should be refused because the member already has 3 active loans.
        extra_book = Book.objects.create(
            library=self.library, title='Extra Book', author='Author', isbn='EXTRA-1',
            category=self.category, total_copies=1, available_copies=1,
        )
        self._borrow(extra_book)
        extra_book.refresh_from_db()
        self.assertEqual(extra_book.available_copies, 1)  # unchanged: borrow was rejected
        self.assertEqual(BorrowRecord.objects.filter(book=extra_book).count(), 0)

    def test_return_on_time_creates_no_fine(self):
        self._borrow(self.book)
        record = BorrowRecord.objects.get(book=self.book, member=self.member)
        self.client.post(reverse('circulation:return_book', args=[record.pk]))
        record.refresh_from_db()
        self.assertEqual(record.status, BorrowRecord.Status.RETURNED)
        self.assertFalse(Fine.objects.filter(borrow_record=record).exists())

    def test_late_return_creates_correct_fine_amount(self):
        self._borrow(self.book)
        record = BorrowRecord.objects.get(book=self.book, member=self.member)
        # Simulate the loan being overdue by 3 days.
        record.due_date = timezone.localdate() - timedelta(days=3)
        record.save()

        self.client.post(reverse('circulation:return_book', args=[record.pk]))
        record.refresh_from_db()
        fine = Fine.objects.get(borrow_record=record)

        from django.conf import settings
        self.assertEqual(fine.amount, 3 * settings.FINE_DAILY_RATE)
        self.assertEqual(fine.payment_status, Fine.PaymentStatus.UNPAID)

    def test_return_increments_available_copies(self):
        self._borrow(self.book)
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 0)

        record = BorrowRecord.objects.get(book=self.book, member=self.member)
        self.client.post(reverse('circulation:return_book', args=[record.pk]))
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 1)

    def test_borrow_sends_confirmation_email(self):
        self._borrow(self.book)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.member.email, mail.outbox[0].to)


class LibraryIsolationTests(CirculationTestCase):
    """Data of one library must never leak into, or be changed from, another."""

    def setUp(self):
        super().setUp()
        self.other = Library.objects.create(name='Library B', code='b')
        self.other_category = Category.objects.create(library=self.other, name='Fiction')
        self.other_book = Book.objects.create(
            library=self.other, title='Other Book', author='X', isbn='1111111111',  # same ISBN as Library A is allowed
            category=self.other_category, total_copies=1, available_copies=1,
        )
        self.other_member = User.objects.create_user(
            username='member_b', password='Member@123', role=User.Role.MEMBER, library=self.other,
        )

    def test_same_isbn_and_category_name_allowed_in_different_libraries(self):
        self.assertEqual(Book.objects.filter(isbn='1111111111').count(), 2)
        self.assertEqual(Category.objects.filter(name='Fiction').count(), 2)

    def test_book_list_shows_only_own_library(self):
        response = self.client.get(reverse('catalog:book_list'))
        titles = [b.title for b in response.context['page_obj']]
        self.assertIn('Test Book', titles)
        self.assertNotIn('Other Book', titles)

    def test_cannot_open_or_edit_other_library_book(self):
        self.assertEqual(self.client.get(reverse('catalog:book_detail', args=[self.other_book.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('catalog:book_update', args=[self.other_book.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('catalog:book_delete', args=[self.other_book.pk])).status_code, 404)
        self.assertTrue(Book.objects.filter(pk=self.other_book.pk).exists())

    def test_cannot_borrow_other_library_book_or_lend_to_other_library_member(self):
        r = self.client.post(reverse('circulation:borrow_book', args=[self.other_book.pk]),
                             {'member_username': self.member.username, 'due_days': 14})
        self.assertEqual(r.status_code, 404)
        # Member of Library B cannot borrow Library A's book.
        self.client.post(reverse('circulation:borrow_book', args=[self.book.pk]),
                         {'member_username': self.other_member.username, 'due_days': 14})
        self.assertEqual(BorrowRecord.objects.count(), 0)

    def test_cannot_return_other_library_loan(self):
        record = BorrowRecord.objects.create(
            member=self.other_member, book=self.other_book, due_date=timezone.localdate(),
        )
        r = self.client.post(reverse('circulation:return_book', args=[record.pk]))
        self.assertEqual(r.status_code, 404)

    def test_reports_only_count_own_library(self):
        BorrowRecord.objects.create(member=self.other_member, book=self.other_book, due_date=timezone.localdate())
        response = self.client.get(reverse('circulation:reports'))
        self.assertEqual(response.context['stats']['total_books'], 1)
        self.assertEqual(response.context['stats']['total_members'], 1)
        self.assertEqual(response.context['stats']['active_loans_count'], 0)


class ExtraFeatureTests(CirculationTestCase):
    """Loan history, renewals, reservation cancel, CSV export."""

    def _loan(self, **kwargs):
        defaults = dict(member=self.member, book=self.book, librarian=self.librarian,
                        due_date=timezone.localdate() + timedelta(days=5))
        defaults.update(kwargs)
        return BorrowRecord.objects.create(**defaults)

    def test_loan_list_search_and_filter(self):
        self._loan()
        self._loan(status=BorrowRecord.Status.RETURNED, return_date=timezone.localdate())
        r = self.client.get(reverse('circulation:loan_list'), {'q': 'member1', 'status': 'RETURNED'})
        self.assertEqual(len(r.context['page_obj']), 1)
        r = self.client.get(reverse('circulation:loan_list'), {'q': 'nobody'})
        self.assertEqual(len(r.context['page_obj']), 0)

    def test_renew_extends_due_date_up_to_limit(self):
        loan = self._loan()
        original = loan.due_date
        for _ in range(3):
            self.client.post(reverse('circulation:renew_loan', args=[loan.pk]))
        loan.refresh_from_db()
        self.assertEqual(loan.renewal_count, 2)
        self.assertEqual(loan.due_date, original + timedelta(days=14))

    def test_cannot_renew_overdue_loan(self):
        loan = self._loan(due_date=timezone.localdate() - timedelta(days=2))
        self.client.post(reverse('circulation:renew_loan', args=[loan.pk]))
        loan.refresh_from_db()
        self.assertEqual(loan.renewal_count, 0)

    def test_cannot_renew_when_someone_else_reserved(self):
        other = User.objects.create_user('member2', password='Member@123', role=User.Role.MEMBER, library=self.library)
        Reservation.objects.create(member=other, book=self.book)
        loan = self._loan()
        self.client.post(reverse('circulation:renew_loan', args=[loan.pk]))
        loan.refresh_from_db()
        self.assertEqual(loan.renewal_count, 0)

    def test_member_can_renew_own_loan_only(self):
        other = User.objects.create_user('member2', password='Member@123', role=User.Role.MEMBER, library=self.library)
        mine, theirs = self._loan(), self._loan(member=other)
        self.client.logout()
        self.client.login(username='member1', password='Member@123')
        self.client.post(reverse('circulation:renew_loan', args=[mine.pk]))
        self.assertEqual(self.client.post(reverse('circulation:renew_loan', args=[theirs.pk])).status_code, 404)
        mine.refresh_from_db()
        self.assertEqual(mine.renewal_count, 1)

    def test_member_can_cancel_own_reservation(self):
        res = Reservation.objects.create(member=self.member, book=self.book)
        self.client.logout()
        self.client.login(username='member1', password='Member@123')
        self.client.post(reverse('circulation:cancel_reservation', args=[res.pk]))
        res.refresh_from_db()
        self.assertEqual(res.status, Reservation.Status.CANCELLED)

    def test_return_notifies_waiting_member(self):
        other = User.objects.create_user('member2', password='Member@123', email='m2@library-system.local',
                                         role=User.Role.MEMBER, library=self.library)
        Reservation.objects.create(member=other, book=self.book)
        loan = self._loan()
        self.client.post(reverse('circulation:return_book', args=[loan.pk]))
        self.assertTrue(any('m2@library-system.local' in m.to for m in mail.outbox))

    def test_csv_exports(self):
        self._loan()
        r = self.client.get(reverse('circulation:export_books'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/csv', r['Content-Type'])
        self.assertIn('Test Book', r.content.decode('utf-8'))
        r = self.client.get(reverse('circulation:export_loans'))
        self.assertIn('member1', r.content.decode('utf-8'))

    def test_member_cannot_export_or_view_loan_list(self):
        self.client.logout()
        self.client.login(username='member1', password='Member@123')
        self.assertEqual(self.client.get(reverse('circulation:export_books')).status_code, 302)
        self.assertEqual(self.client.get(reverse('circulation:loan_list')).status_code, 302)

    def test_password_change(self):
        self.client.logout()
        self.client.login(username='member1', password='Member@123')
        r = self.client.post(reverse('accounts:password_change'), {
            'old_password': 'Member@123', 'new_password1': 'BrandNew#Pass987', 'new_password2': 'BrandNew#Pass987',
        })
        self.assertRedirects(r, reverse('accounts:profile'))
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password('BrandNew#Pass987'))
