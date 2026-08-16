from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from product_intelligence.models import (
    ProductOpportunity,
)


class Command(BaseCommand):
    help = (
        "Supprime les images orphelines du dossier "
        "media/product_opportunities."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=(
                "Affiche les fichiers qui seraient supprimés "
                "sans les supprimer."
            ),
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        folder = (
            Path(settings.MEDIA_ROOT)
            / "product_opportunities"
        )

        if not folder.exists():
            self.stdout.write(
                self.style.SUCCESS(
                    "Aucun dossier product_opportunities à nettoyer."
                )
            )
            return

        used_files = {
            Path(image_name).name
            for image_name in (
                ProductOpportunity.objects
                .exclude(image="")
                .values_list(
                    "image",
                    flat=True,
                )
            )
            if image_name
        }

        files = [
            path
            for path in folder.iterdir()
            if path.is_file()
        ]

        orphan_files = [
            path
            for path in files
            if path.name not in used_files
        ]

        if not orphan_files:
            self.stdout.write(
                self.style.SUCCESS(
                    "Aucune image orpheline trouvée."
                )
            )
            return

        deleted_count = 0

        for path in orphan_files:
            if dry_run:
                self.stdout.write(
                    f"ORPHAN: {path.name}"
                )
                continue

            path.unlink()

            deleted_count += 1

            self.stdout.write(
                f"SUPPRIME: {path.name}"
            )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    (
                        f"{len(orphan_files)} image(s) "
                        "orpheline(s) détectée(s). "
                        "Aucune suppression effectuée."
                    )
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    (
                        f"{deleted_count} image(s) "
                        "orpheline(s) supprimée(s)."
                    )
                )
            )
            