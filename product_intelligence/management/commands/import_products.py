from django.core.management.base import BaseCommand

from product_intelligence.providers.fake_provider import (
    FakeProvider,
)
from product_intelligence.services.importer import (
    OpportunityImporter,
)


class Command(BaseCommand):
    help = "Importe des opportunités depuis le fournisseur fictif."

    def handle(self, *args, **options):
        provider = FakeProvider()

        result = OpportunityImporter.import_from_provider(
            provider
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"{result['created']} opportunité(s) créée(s), "
                    f"{result['skipped']} ignorée(s)."
                )
            )
        )
        