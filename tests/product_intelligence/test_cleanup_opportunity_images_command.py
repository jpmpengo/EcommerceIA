import tempfile
from pathlib import Path

from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.core.management import call_command
from django.test import (
    TestCase,
    override_settings,
)

from product_intelligence.models import (
    ProductOpportunity,
)

from decimal import Decimal

class CleanupOpportunityImagesCommandTests(TestCase):

    def test_dry_run_reports_orphan_without_deleting_it(
        self,
    ):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(
                MEDIA_ROOT=media_root,
            ):
                folder = (
                    Path(media_root)
                    / "product_opportunities"
                )
                folder.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                orphan = folder / "orphan.jpg"

                orphan.write_bytes(
                    b"fake-image"
                )

                self.assertTrue(
                    orphan.exists()
                )

                call_command(
                    "cleanup_opportunity_images",
                    "--dry-run",
                )

                self.assertTrue(
                    orphan.exists()
                )

    def test_deletes_orphan_but_keeps_used_image(
        self,
    ):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(
                MEDIA_ROOT=media_root,
            ):
                opportunity = (
                    ProductOpportunity.objects.create(
                        name="Wireless Charger",
                        source_name="CJdropshipping",
                        supplier_price=Decimal("4.53"),
                        market_price=Decimal("27.90"),
                    )
                )

                opportunity.image = (
                    SimpleUploadedFile(
                        "used.jpg",
                        b"used-image",
                        content_type="image/jpeg",
                    )
                )

                opportunity.save(
                    update_fields=[
                        "image",
                        "updated_at",
                    ]
                )

                used_path = Path(
                    opportunity.image.path
                )

                folder = used_path.parent

                orphan_path = (
                    folder
                    / "orphan.jpg"
                )

                orphan_path.write_bytes(
                    b"orphan-image"
                )

                call_command(
                    "cleanup_opportunity_images",
                )

                self.assertTrue(
                    used_path.exists()
                )

                self.assertFalse(
                    orphan_path.exists()
                )

