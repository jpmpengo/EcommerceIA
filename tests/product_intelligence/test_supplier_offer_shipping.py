from decimal import Decimal
from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.supplier_offer_shipping import (
    SupplierOfferShippingService,
)


class SupplierOfferShippingServiceTests(
    SimpleTestCase
):

    def test_persists_shipping_quote(
        self,
    ):
        offer = Mock()
        offer.currency = "USD"

        estimation_service = Mock()

        estimation_service.estimate.return_value = {
            "cost": Decimal("4.25"),
            "currency": "USD",
            "shipping_days": 12,
            "shipping_country": "FR",
            "method": "CJPacket",
        }

        service = SupplierOfferShippingService(
            estimation_service=(
                estimation_service
            )
        )

        result = service.enrich(
            supplier_offer=offer,
            destination_country="FR",
        )

        estimation_service.estimate.assert_called_once_with(
            offer=offer,
            destination_country="FR",
            quantity=1,
        )

        self.assertEqual(
            offer.shipping_cost,
            Decimal("4.25"),
        )

        self.assertEqual(
            offer.shipping_days,
            12,
        )

        self.assertEqual(
            offer.shipping_country,
            "FR",
        )

        offer.save.assert_called_once_with(
            update_fields=[
                "shipping_cost",
                "shipping_days",
                "shipping_country",
            ]
        )

        self.assertEqual(
            result,
            {
                "status": "estimated",
                "cost": Decimal("4.25"),
                "currency": "USD",
                "shipping_days": 12,
                "shipping_country": "FR",
                "method": "CJPacket",
            },
        )

    def test_reports_unavailable_quote(
        self,
    ):
        offer = Mock()
        offer.currency = "USD"

        estimation_service = Mock()
        estimation_service.estimate.return_value = None

        service = SupplierOfferShippingService(
            estimation_service=(
                estimation_service
            )
        )

        result = service.enrich(
            supplier_offer=offer,
            destination_country="FR",
        )

        offer.save.assert_not_called()

        self.assertEqual(
            result,
            {
                "status": "unavailable",
                "reason": (
                    "Aucun devis de livraison "
                    "disponible."
                ),
            },
        )

    def test_rejects_shipping_currency_mismatch(
        self,
    ):
        offer = Mock()
        offer.currency = "EUR"

        estimation_service = Mock()

        estimation_service.estimate.return_value = {
            "cost": Decimal("4.25"),
            "currency": "USD",
            "shipping_days": 12,
            "shipping_country": "FR",
            "method": "CJPacket",
        }

        service = SupplierOfferShippingService(
            estimation_service=(
                estimation_service
            )
        )

        result = service.enrich(
            supplier_offer=offer,
            destination_country="FR",
        )

        offer.save.assert_not_called()

        self.assertEqual(
            result,
            {
                "status": "currency_mismatch",
                "reason": (
                    "La devise du devis de "
                    "livraison ne correspond pas "
                    "à celle de l’offre."
                ),
            },
        )