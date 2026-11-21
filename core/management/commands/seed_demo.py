from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from catalog.models import Category, Book
from core.models import Library

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with demo users, categories and books for Library System."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        # ---- Library ----
        library, _ = Library.objects.get_or_create(
            code='main', defaults={'name': 'Main Library', 'address': ''},
        )

        # ---- Users (created if missing; password/role/active status are reset every run) ----
        demo_users = [
            dict(username='admin', password='Admin@12345', first_name='System', last_name='Administrator',
                 role=User.Role.ADMIN, is_staff=True, is_superuser=True, library=None),
            dict(username='librarian1', password='Librarian@123', first_name='Amina', last_name='Warsame',
                 role=User.Role.LIBRARIAN, is_staff=True, is_superuser=False, library=library),
            dict(username='member1', password='Member@123', first_name='Huda', last_name='Osman',
                 role=User.Role.MEMBER, is_staff=False, is_superuser=False, library=library,
                 membership_type=User.MembershipType.STUDENT),
        ]
        for data in demo_users:
            data = dict(data)
            username, password = data.pop('username'), data.pop('password')
            user, created = User.objects.get_or_create(username=username)
            for field, value in data.items():
                setattr(user, field, value)
            user.email = f'{username}@library-system.local'
            user.is_active = True
            user.status = User.Status.ACTIVE
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f"{'Created' if created else 'Reset'} {username} ({username} / {password})"))

        from django.core.management import call_command
        call_command('create_laab')

        # ---- Categories ----
        category_names = [
            ("Fiction", "Sheekooyin khayaali ah"),
            ("Non-Fiction", "Buugaag xaqiiqo ku salaysan"),
            ("Science", "Sayniska iyo cilmiga"),
            ("Technology", "Tignoolajiyada iyo Kombuyuutarka"),
            ("History", "Taariikhda"),
            ("Islamic Studies", "Cilmiga Islaamka"),
        ]
        categories = {}
        for name, desc in category_names:
            cat, _ = Category.objects.get_or_create(library=library, name=name, defaults={'description': desc})
            categories[name] = cat

        # ---- Books ----
        books = [
            ("Things Fall Apart", "Chinua Achebe", "9780435905255", "Fiction", "Heinemann", 1958, 3, "A1-01"),
            ("A Brief History of Time", "Stephen Hawking", "9780553380163", "Science", "Bantam", 1988, 2, "B2-04"),
            ("Clean Code", "Robert C. Martin", "9780132350884", "Technology", "Prentice Hall", 2008, 4, "C3-12"),
            ("Django for Beginners", "William S. Vincent", "9781735467207", "Technology", "WelcomeToCode", 2022, 3, "C3-15"),
            ("Sapiens", "Yuval Noah Harari", "9780062316097", "Non-Fiction", "Harper", 2015, 5, "B1-08"),
            ("The Prophet's Biography", "Ibn Hisham", "9789960899558", "Islamic Studies", "Darussalam", 2000, 4, "D1-02"),
            ("A History of Africa", "J.D. Fage", "9780415252485", "History", "Routledge", 2001, 2, "E2-06"),
            ("Introduction to Algorithms", "Thomas H. Cormen", "9780262033848", "Technology", "MIT Press", 2009, 3, "C3-20"),
            ("The Alchemist", "Paulo Coelho", "9780061122415", "Fiction", "HarperOne", 1988, 4, "A1-05"),
            ("Cosmos", "Carl Sagan", "9780345539434", "Science", "Ballantine", 1980, 2, "B2-09"),
            ("Somalia: A Country Study", "Helen Chapin Metz", "9780844407753", "History", "Federal Research", 1993, 1, "E2-11"),
            ("Riyad as-Salihin", "Imam An-Nawawi", "9789960899121", "Islamic Studies", "Darussalam", 1999, 5, "D1-07"),
        ]
        created_count = 0
        for title, author, isbn, cat_name, publisher, year, copies, shelf in books:
            _, created = Book.objects.get_or_create(
                library=library, isbn=isbn,
                defaults={
                    'title': title, 'author': author, 'category': categories[cat_name],
                    'publisher': publisher, 'year_published': year,
                    'total_copies': copies, 'available_copies': copies,
                    'shelf_location': shelf,
                },
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. {created_count} new books added. Categories: {Category.objects.filter(library=library).count()}."
        ))
