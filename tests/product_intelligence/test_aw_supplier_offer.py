from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import Supplier
from product_intelligence.services.aw_supplier_offer import (
    AWSupplierOfferService,
)


class AWSupplierOfferServiceTests(TestCase):

    def test_persists_aw_product_fields(self):
        supplier = Supplier.objects.create(
            name="AW Dropship",
            country="SK",
            supplier_type="dropshipper",
        )

        product = {
            "id": 188999,
            "code": "MacP-03",
            "name": "Macrame Pot Holder - Lrg Single Beaded",
            "price": "10.96",
            "current_stock": 128,
            "gross_weight": 230,
            "currency_code": "EUR",
            "ean_barcode": "5055796597338",
            "image": {
                "original": "https://example.com/macp-03.jpg",
            },
        }

        offer = AWSupplierOfferService().create_offer(
            supplier=supplier,
            product=product,
        )

        self.assertEqual(
            offer.purchase_price,
            Decimal("10.96"),
        )
        self.assertEqual(
            offer.product_name,
            "Macrame Pot Holder - Lrg Single Beaded",
        )
        self.assertEqual(offer.currency, "EUR")
        self.assertEqual(
            offer.supplier_product_id,
            "188999",
        )
        self.assertEqual(
            offer.supplier_sku,
            "MacP-03",
        )
        self.assertEqual(offer.stock, 128)
        self.assertTrue(offer.is_available)
        self.assertEqual(
            offer.shipping_weight_grams,
            230,
        )
        self.assertEqual(
            offer.stock_country,
            "",
        )
        self.assertEqual(
            offer.image_url,
            "https://example.com/macp-03.jpg",
        )

    def test_updates_existing_aw_offer_instead_of_duplicating(self):
        from product_intelligence.models import ProductIdea, SupplierOffer
        idea = ProductIdea.objects.create(name="Idea", customer_problem="P", target_customer="C", reason_to_study="R", countries=["FR"], status="selected")
        supplier = Supplier.objects.create(name="AW Dropship", country="SK", supplier_type="dropshipper")
        product = {"id": 188999, "code": "MacP-03", "name": "Macrame Pot Holder", "price": "10.96", "current_stock": 128, "gross_weight": 230, "currency_code": "EUR"}
        service = AWSupplierOfferService()
        first = service.create_offer(supplier=supplier, product=product, product_idea=idea)
        product["price"] = "11.25"
        product["current_stock"] = 120
        second = service.create_offer(supplier=supplier, product=product, product_idea=idea)
        self.assertEqual(first.id, second.id)
        self.assertEqual(SupplierOffer.objects.filter(supplier=supplier, product_idea=idea, supplier_product_id="188999").count(), 1)
        second.refresh_from_db()
        self.assertEqual(second.purchase_price, Decimal("11.25"))
        self.assertEqual(second.stock, 120)

    def test_persists_aw_comparability_features(self):
        supplier = Supplier.objects.create(name="AW Dropship", country="SK", supplier_type="dropshipper")
        product = {"id": 189001, "code": "MacP-05", "name": "Macrame Pot Holder - Large Pot Holder - Extra Long", "price": "16.26", "current_stock": 106, "gross_weight": 170, "currency_code": "EUR", "description": "Macrame plant hangers. Plant and pot in picture not included."}
        offer = AWSupplierOfferService().create_offer(supplier=supplier, product=product)
        self.assertEqual(offer.variant_features["product_family"], "macrame_hanger")
        self.assertFalse(offer.variant_features["includes_pot"])

    def test_update_preserves_existing_shipping_cost(self):
        supplier = Supplier.objects.create(name="AW Dropship", country="SK", supplier_type="dropshipper")
        product = {"id": 188999, "code": "MacP-03", "name": "Macrame Pot Holder", "price": "10.96", "current_stock": 128, "gross_weight": 230, "currency_code": "EUR"}
        service = AWSupplierOfferService()
        offer = service.create_offer(supplier=supplier, product=product)
        offer.shipping_cost = Decimal("7.50")
        offer.save(update_fields=["shipping_cost"])
        updated = service.create_offer(supplier=supplier, product=product)
        self.assertEqual(updated.shipping_cost, Decimal("7.50"))

    def test_persists_supplier_search_keyword(self):
        supplier = Supplier.objects.create(
            name="AW Dropship",
            country="SK",
            supplier_type="dropshipper",
        )
        product = {
            "id": 188999,
            "code": "BIKE-01",
            "name": "USB Bike Light",
            "price": "10.96",
            "current_stock": 128,
            "gross_weight": 230,
            "currency_code": "EUR",
        }
        offer = AWSupplierOfferService().create_offer(
            supplier=supplier,
            product=product,
            supplier_search_keyword="USB rechargeable bike light",
        )
        self.assertEqual(
            offer.supplier_search_keyword,
            "USB rechargeable bike light",
        )
