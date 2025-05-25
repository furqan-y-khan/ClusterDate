from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Profile

class Command(BaseCommand):
    help = 'Creates core profiles for users who do not have one'

    def handle(self, *args, **kwargs):
        # Get all users
        users = User.objects.all()
        created_count = 0
        existing_count = 0
        
        for user in users:
            # Check if user has a profile
            try:
                user.profile
                existing_count += 1
            except Profile.DoesNotExist:
                # Create profile if it doesn't exist
                Profile.objects.create(user=user)
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created profile for user: {user.username}'))
        
        self.stdout.write(self.style.SUCCESS(f'Process completed. Created {created_count} profiles. {existing_count} profiles already existed.')) 