from decimal import Decimal
from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.supplier_offer_evaluation import (
    SupplierOfferEvaluationService,
)


class SupplierOfferEvaluationServiceTests(
    SimpleTestCase
):

    def _build_offer(
        self,
        currency="USD",
        shipping_cost=None,
    ):
        supplier_offer = Mock()

        supplier_offer.pk = 213
        supplier_offer.product_name = (
            "9-hole Space Saving Hanger"
        )
        supplier_offer.purchase_price = (
            Decimal("0.27")
        )
        supplier_offer.currency = currency
        supplier_offer.shipping_cost = (
            shipping_cost
        )
        supplier_offer.stock = 36901
        supplier_offer.supplier.name = (
            "CJdropshipping"
        )

        return supplier_offer

    def _build_summary(
        self,
    ):
        return {
            "currency": "EUR",
            "retained_count": 5,
            "minimum_price": Decimal("10.62"),
            "median_price": Decimal("16.21"),
            "maximum_price": Decimal("17.99"),
            "source_domain_count": 4,
        }

    def test_uses_configured_price_policy(
        self,
    ):
        supplier_offer = self._build_offer()

        summary = self._build_summary()

        summary_service = Mock()
        summary_service.summarize.return_value = (
            summary
        )

        reference_service = Mock()
        reference_service.select.return_value = (
            Decimal("10.62")
        )

        service = SupplierOfferEvaluationService(
            summary_service=summary_service,
            reference_service=reference_service,
            price_policy="minimum",
        )

        dossier = service.prepare(
            supplier_offer=supplier_offer,
            market_currency="EUR",
        )

        reference_service.select.assert_called_once_with(
            summary=summary,
            policy="minimum",
        )

        self.assertEqual(
            dossier["decision_price_policy"],
            "minimum",
        )

        self.assertEqual(
            dossier["decision_price"],
            Decimal("10.62"),
        )

        self.assertEqual(
            dossier["market"]["minimum_price"],
            Decimal("10.62"),
        )

        self.assertEqual(
            dossier["market"]["median_price"],
            Decimal("16.21"),
        )

        self.assertEqual(
            dossier["market"]["maximum_price"],
            Decimal("17.99"),
        )

    def test_marks_dossier_incomplete_when_cost_data_is_missing(
        self,
    ):
        supplier_offer = self._build_offer(
            currency="USD",
            shipping_cost=None,
        )

        summary_service = Mock()
        summary_service.summarize.return_value = (
            self._build_summary()
        )

        reference_service = Mock()
        reference_service.select.return_value = (
            Decimal("10.62")
        )

        service = SupplierOfferEvaluationService(
            summary_service=summary_service,
            reference_service=reference_service,
            price_policy="minimum",
        )

        dossier = service.prepare(
            supplier_offer=supplier_offer,
            market_currency="EUR",
        )

        self.assertEqual(
            dossier["status"],
            "incomplete",
        )

        self.assertEqual(
            dossier["blockers"],
            [
                "Coût de livraison manquant.",
                "Conversion USD vers EUR requise.",
            ],
        )

    def test_marks_dossier_ready_for_cost_analysis(
        self,
    ):
        supplier_offer = self._build_offer(
            currency="EUR",
            shipping_cost=Decimal("2.50"),
        )

        summary_service = Mock()
        summary_service.summarize.return_value = (
            self._build_summary()
        )

        reference_service = Mock()
        reference_service.select.return_value = (
            Decimal("10.62")
        )

        service = SupplierOfferEvaluationService(
            summary_service=summary_service,
            reference_service=reference_service,
            price_policy="minimum",
        )

        dossier = service.prepare(
            supplier_offer=supplier_offer,
            market_currency="EUR",
        )

        self.assertEqual(
            dossier["status"],
            "ready_for_cost_analysis",
        )

        self.assertEqual(
            dossier["blockers"],
            [],
        )

    def test_blocks_insufficient_market_evidence(
        self,
    ):
        supplier_offer = self._build_offer(
            currency="EUR",
            shipping_cost=Decimal("2.50"),
        )

        summary = self._build_summary()
        summary["retained_count"] = 1
        summary["source_domain_count"] = 1

        summary_service = Mock()
        summary_service.summarize.return_value = (
            summary
        )

        reference_service = Mock()
        reference_service.select.return_value = (
            Decimal("10.62")
        )

        service = SupplierOfferEvaluationService(
            summary_service=summary_service,
            reference_service=reference_service,
            price_policy="minimum",
        )

        dossier = service.prepare(
            supplier_offer=supplier_offer,
            market_currency="EUR",
        )

        self.assertEqual(
            dossier["status"],
            "incomplete",
        )

        self.assertIn(
            (
                "Au moins trois prix comparables "
                "sont nécessaires."
            ),
            dossier["blockers"],
        )

        self.assertIn(
            (
                "Au moins deux domaines sources "
                "sont nécessaires."
            ),
            dossier["blockers"],
        )