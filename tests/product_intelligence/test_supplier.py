from django.test import TestCase

from product_intelligence.models import Supplier


class SupplierTests(TestCase):

    def test_supplier_can_be_created(self):
        supplier = Supplier.objects.create(
            name="Fournisseur Test",
            country="FR",
            website="https://example.com",
            supplier_type="wholesaler",
        )

        self.assertEqual(
            supplier.name,
            "Fournisseur Test",
        )

        self.assertEqual(
            supplier.country,
            "FR",
        )

        self.assertEqual(
            supplier.supplier_type,
            "wholesaler",
        )

        self.assertEqual(
            str(supplier),
            "Fournisseur Test",
        )

        