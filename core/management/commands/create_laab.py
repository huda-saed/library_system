from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create (or reset) the Laab admin user: username 'Laab', password 'laab6849a'."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username='Laab')
        user.role = User.Role.ADMIN
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.status = User.Status.ACTIVE
        user.set_password('laab6849a')
        user.save()
        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Updated'} user Laab (Laab / laab6849a)"
        ))
