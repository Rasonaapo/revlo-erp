from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Test database connection'

    def handle(self, *args, **kwargs):
        try:
            connection.ensure_connection()
            self.stdout.write(self.style.SUCCESS('Database connection successful!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to database: {e}'))
