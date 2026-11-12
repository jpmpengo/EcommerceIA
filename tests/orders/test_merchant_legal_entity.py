from django.test import TestCase

from orders.models import MerchantLegalEntity


class MerchantLegalEntityTests(TestCase):

    def test_can_store_active_french_merchant_legal_entity(self):
        merchant = MerchantLegalEntity.objects.create(
            legal_name="EcommerceIA Demo SAS",
            trade_name="EcommerceIA",
            siren="123456789",
            siret="12345678900010",
            vat_number="FR00123456789",
            address="10 rue du Commerce",
            postal_code="75001",
            city="Paris",
            country="FR",
            email="contact@ecommerceia.local",
            phone="0102030405",
            is_active=True,
        )

        self.assertEqual(merchant.legal_name, "EcommerceIA Demo SAS")
        self.assertEqual(merchant.trade_name, "EcommerceIA")
        self.assertEqual(merchant.siren, "123456789")
        self.assertEqual(merchant.siret, "12345678900010")
        self.assertEqual(merchant.country, "FR")
        self.assertTrue(merchant.is_active)


    def test_only_one_merchant_legal_entity_can_be_active(self):
        MerchantLegalEntity.objects.create(
            legal_name="EcommerceIA Demo SAS",
            trade_name="EcommerceIA",
            siren="123456789",
            siret="12345678900010",
            address="10 rue du Commerce",
            postal_code="75001",
            city="Paris",
            country="FR",
            is_active=True,
        )

        with self.assertRaises(Exception):
            MerchantLegalEntity.objects.create(
                legal_name="Autre Société Demo",
                trade_name="Autre",
                siren="987654321",
                siret="98765432100011",
                address="20 rue de Test",
                postal_code="69001",
                city="Lyon",
                country="FR",
                is_active=True,
            )


    def test_get_active_returns_current_merchant(self):
        merchant = MerchantLegalEntity.objects.create(
            legal_name="EcommerceIA Demo SAS",
            address="10 rue du Commerce",
            postal_code="75001",
            city="Paris",
            country="FR",
            is_active=True,
        )

        self.assertEqual(MerchantLegalEntity.get_active(), merchant)
