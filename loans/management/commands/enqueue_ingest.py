from django.core.management.base import BaseCommand
from loans.tasks import ingest_excel_data


class Command(BaseCommand):
    help = 'Enqueue Excel data ingestion task'

    def handle(self, *args, **options):
        # Enqueue the task
        task = ingest_excel_data.delay()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully enqueued ingestion task with ID: {task.id}')
        )
