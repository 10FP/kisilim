from django.core.management.base import BaseCommand

from assessment.views import bootstrap_demo_data


class Command(BaseCommand):
    help = "Örnek ders, LO, PO, not bileşenleri ve katkılarını veritabanına yükler."

    def handle(self, *args, **options):
        bootstrap_demo_data()
        self.stdout.write(self.style.SUCCESS("Demo verileri yüklendi (idempotent)."))
