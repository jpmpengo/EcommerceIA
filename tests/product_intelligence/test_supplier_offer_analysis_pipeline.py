from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

from django.test import SimpleTestCase

from product_intelligence.services.supplier_offer_analysis_pipeline import (
    SupplierOfferAnalysisPipeline,
)


class SupplierOfferAnalysisPipelineTests(SimpleTestCase):

    def test_converts_costs_and_creates_analyzed_opportunity(self):
        offer = Mock()

        evaluation_service = Mock()
        batch_id = "11111111-1111-1111-1111-111111111111"
        evaluation_service.prepare.return_value = {
            "decision_price": Decimal("14.99"),
            "blockers": [
                "Conversion USD vers EUR requise."
            ],
            "warnings": ["Livraison lente."],
            "market": {
                "collection_batch_id": batch_id,
            },
        }

        base_cost_service = Mock()
        base_cost_service.calculate.return_value = {
            "purchase_converted": Decimal("0.98"),
            "shipping_converted": Decimal("4.45"),
            "base_cost": Decimal("5.43"),
        }

        cost_service = Mock()
        cost_service.calculate.return_value = {
            "projected_profit": Decimal("5.35"),
        }

        opportunity = Mock(pk=87)
        opportunity_service = Mock()
        opportunity_service.create_analyzed_opportunity.return_value = (
            opportunity
        )

        pipeline = SupplierOfferAnalysisPipeline(
            evaluation_service=evaluation_service,
            base_cost_service=base_cost_service,
            cost_calculation_service=cost_service,
            opportunity_service=opportunity_service,
        )

        result = pipeline.process(
            supplier_offer=offer,
            market_currency="EUR",
            create=True,
        )

        self.assertEqual(result["status"], "created")
        self.assertEqual(result["opportunity"], opportunity)
        base_cost_service.calculate.assert_called_once_with(
            supplier_offer=offer,
            target_currency="EUR",
        )
        cost_service.calculate.assert_called_once_with(
            decision_price=Decimal("14.99"),
            base_cost=Decimal("5.43"),
            currency="EUR",
        )
        opportunity_service.create_analyzed_opportunity.assert_called_once_with(
            offer=offer,
            decision_price=Decimal("14.99"),
            base_cost_result=base_cost_service.calculate.return_value,
            cost_result=cost_service.calculate.return_value,
            market_collection_batch_id=batch_id,
            market_summary=evaluation_service.prepare.return_value["market"],
        )

    def test_keeps_market_collection_batch_id_in_result_dossier(self):
        batch_id = uuid4()
        offer = Mock()

        evaluation_service = Mock()
        evaluation_service.prepare.return_value = {
            "decision_price": Decimal("14.99"),
            "blockers": [],
            "warnings": [],
            "market": {
                "collection_batch_id": batch_id,
            },
        }

        base_cost_service = Mock()
        base_cost_service.calculate.return_value = {
            "purchase_converted": Decimal("1.00"),
            "shipping_converted": Decimal("2.00"),
            "base_cost": Decimal("3.00"),
        }

        cost_service = Mock()
        cost_service.calculate.return_value = {
            "projected_profit": Decimal("5.00"),
            "projected_margin_rate": Decimal("30.00"),
        }

        pipeline = SupplierOfferAnalysisPipeline(
            evaluation_service=evaluation_service,
            base_cost_service=base_cost_service,
            cost_calculation_service=cost_service,
            opportunity_service=Mock(),
        )

        result = pipeline.process(offer)

        self.assertEqual(
            result["dossier"]["market"]["collection_batch_id"],
            batch_id,
        )

    def test_marks_dossier_ready_for_opportunity_after_profitable_analysis(self):
        offer = Mock()
        evaluation_service = Mock()
        evaluation_service.prepare.return_value = {
            "decision_price": Decimal("12.36"),
            "blockers": [],
            "warnings": [],
            "status": "ready_for_cost_analysis",
            "market": {},
        }
        base_cost_service = Mock()
        base_cost_service.calculate.return_value = {
            "purchase_converted": Decimal("7.82"),
            "shipping_converted": Decimal("0.00"),
            "base_cost": Decimal("7.82"),
        }
        cost_service = Mock()
        cost_service.calculate.return_value = {
            "projected_profit": Decimal("1.03"),
            "projected_margin_rate": Decimal("10.00"),
        }
        pipeline = SupplierOfferAnalysisPipeline(
            evaluation_service=evaluation_service,
            base_cost_service=base_cost_service,
            cost_calculation_service=cost_service,
            opportunity_service=Mock(),
        )

        result = pipeline.process(offer)

        self.assertEqual(result["status"], "ready_for_opportunity")
        self.assertEqual(result["dossier"]["status"], "ready_for_opportunity")

    def test_clears_currency_only_blocker_from_dossier_before_cost_analysis(self):
        offer = Mock()
        evaluation_service = Mock()
        evaluation_service.prepare.return_value = {
            "decision_price": Decimal("12.36"),
            "blockers": ["Conversion USD vers EUR requise."],
            "warnings": [],
            "status": "incomplete",
            "market": {},
        }
        base_cost_service = Mock()
        base_cost_service.calculate.return_value = {
            "purchase_converted": Decimal("7.82"),
            "shipping_converted": Decimal("0.00"),
            "base_cost": Decimal("7.82"),
        }
        cost_service = Mock()
        cost_service.calculate.return_value = {
            "projected_profit": Decimal("1.03"),
            "projected_margin_rate": Decimal("10.00"),
        }
        pipeline = SupplierOfferAnalysisPipeline(
            evaluation_service=evaluation_service,
            base_cost_service=base_cost_service,
            cost_calculation_service=cost_service,
            opportunity_service=Mock(),
        )

        result = pipeline.process(offer)

        self.assertEqual(result["dossier"]["blockers"], [])
        self.assertEqual(result["dossier"]["status"], "ready_for_opportunity")

    def test_stops_on_non_currency_blocker(self):
        evaluation_service = Mock()
        evaluation_service.prepare.return_value = {
            "decision_price": None,
            "blockers": ["Coût de livraison manquant."],
            "warnings": [],
        }

        pipeline = SupplierOfferAnalysisPipeline(
            evaluation_service=evaluation_service,
            base_cost_service=Mock(),
            cost_calculation_service=Mock(),
            opportunity_service=Mock(),
        )

        result = pipeline.process(Mock())

        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(
            result["blockers"],
            ["Coût de livraison manquant."],
        )
        pipeline.base_cost_service.calculate.assert_not_called()

    def test_does_not_add_customs_when_shipping_already_includes_duties(self):
        offer = Mock()
        offer.supplier.country = "CN"
        offer.stock_country = "CN"
        offer.shipping_country = "FR"
        offer.customs_included = True
        evaluation_service = Mock()
        evaluation_service.prepare.return_value = {
            "decision_price": Decimal("25.00"),
            "blockers": [],
            "warnings": [],
            "market": {},
        }
        base_cost_service = Mock()
        base_cost_service.calculate.return_value = {
            "purchase_converted": Decimal("2.69"),
            "shipping_converted": Decimal("10.61"),
            "base_cost": Decimal("13.30"),
        }
        customs_service = Mock()
        cost_service = Mock()
        cost_service.calculate.return_value = {
            "projected_profit": Decimal("2.00"),
            "projected_margin_rate": Decimal("10.00"),
        }
        pipeline = SupplierOfferAnalysisPipeline(
            evaluation_service=evaluation_service,
            base_cost_service=base_cost_service,
            cost_calculation_service=cost_service,
            opportunity_service=Mock(),
            customs_duty_service=customs_service,
        )

        pipeline.process(offer)

        customs_service.estimate.assert_not_called()
        cost_service.calculate.assert_called_once_with(
            decision_price=Decimal("25.00"),
            base_cost=Decimal("13.30"),
            currency="EUR",
            import_duty=Decimal("0.00"),
        )

    def test_uses_european_stock_country_as_customs_origin(self):
        for stock_country in ["FR", "DE", "ES", "RO"]:
            with self.subTest(stock_country=stock_country):
                offer = Mock()
                offer.supplier.country = "CN"
                offer.stock_country = stock_country
                offer.shipping_country = "FR"
                evaluation_service = Mock()
                evaluation_service.prepare.return_value = {
                    "decision_price": Decimal("19.90"),
                    "blockers": [],
                    "warnings": [],
                }
                base_cost_service = Mock()
                base_cost_service.calculate.return_value = {
                    "purchase_converted": Decimal("7.82"),
                    "shipping_converted": Decimal("0.00"),
                    "base_cost": Decimal("7.82"),
                }
                customs_service = Mock()
                customs_service.estimate.return_value = {"amount": Decimal("0.00")}
                cost_service = Mock()
                cost_service.calculate.return_value = {
                    "projected_profit": Decimal("5.00"),
                    "projected_margin_rate": Decimal("30.00"),
                }
                pipeline = SupplierOfferAnalysisPipeline(
                    evaluation_service=evaluation_service,
                    base_cost_service=base_cost_service,
                    cost_calculation_service=cost_service,
                    opportunity_service=Mock(),
                    customs_duty_service=customs_service,
                )
                pipeline.process(offer)
                customs_service.estimate.assert_called_once_with(
                    origin_country=stock_country,
                    destination_country="FR",
                    intrinsic_value=Decimal("7.82"),
                    quantity=1,
                )

    def test_includes_customs_and_blocks_loss_before_creation(self):
        offer = Mock()
        offer.supplier.country = "CN"
        offer.shipping_country = "FR"
        evaluation_service = Mock()
        evaluation_service.prepare.return_value = {
            "decision_price": Decimal("8.00"),
            "blockers": [],
            "warnings": [],
        }
        base_cost_service = Mock()
        base_cost_service.calculate.return_value = {
            "purchase_converted": Decimal("2.00"),
            "shipping_converted": Decimal("4.00"),
            "base_cost": Decimal("6.00"),
        }
        customs_service = Mock()
        customs_service.estimate.return_value = {
            "amount": Decimal("3.00"),
        }
        cost_service = Mock()
        cost_service.calculate.return_value = {
            "projected_profit": Decimal("-2.00"),
            "projected_margin_rate": Decimal("-30.00"),
        }
        opportunity_service = Mock()
        pipeline = SupplierOfferAnalysisPipeline(
            evaluation_service=evaluation_service,
            base_cost_service=base_cost_service,
            cost_calculation_service=cost_service,
            opportunity_service=opportunity_service,
            customs_duty_service=customs_service,
        )

        result = pipeline.process(offer, create=True)

        self.assertEqual(result["status"], "unprofitable")
        self.assertIn("Vente à perte", result["blockers"][0])
        opportunity_service.create_analyzed_opportunity.assert_not_called()
        cost_service.calculate.assert_called_once_with(
            decision_price=Decimal("8.00"),
            base_cost=Decimal("6.00"),
            currency="EUR",
            import_duty=Decimal("3.00"),
        )

    def test_uses_minimum_profitable_price_when_market_minimum_is_not_profitable(self):
        offer = Mock()
        offer.supplier.country = "DE"
        offer.stock_country = "DE"
        offer.shipping_country = "FR"
        evaluation_service = Mock()
        evaluation_service.prepare.return_value = {
            "decision_price": Decimal("9.84"),
            "decision_price_policy": "minimum",
            "blockers": [],
            "warnings": [],
            "market": {
                "minimum_price": Decimal("9.84"),
                "median_price": Decimal("12.40"),
                "maximum_price": Decimal("34.99"),
            },
        }
        base_cost_service = Mock()
        base_cost_service.calculate.return_value = {
            "purchase_converted": Decimal("7.82"),
            "shipping_converted": Decimal("0.00"),
            "base_cost": Decimal("7.82"),
        }
        customs_service = Mock()
        customs_service.estimate.return_value = {"amount": Decimal("0.00")}
        cost_service = Mock()
        cost_service.calculate.return_value = {
            "projected_profit": Decimal("-0.90"),
            "projected_margin_rate": Decimal("-10.98"),
        }
        profitable_price_service = Mock()
        profitable_price_service.calculate.return_value = {
            "decision_price": Decimal("12.36"),
            "cost_analysis": {
                "projected_profit": Decimal("1.03"),
                "projected_margin_rate": Decimal("10.00"),
            },
        }
        pipeline = SupplierOfferAnalysisPipeline(
            evaluation_service=evaluation_service,
            base_cost_service=base_cost_service,
            cost_calculation_service=cost_service,
            opportunity_service=Mock(),
            customs_duty_service=customs_service,
            minimum_profitable_price_service=profitable_price_service,
        )

        result = pipeline.process(offer)

        self.assertEqual(result["status"], "ready_for_opportunity")
        self.assertEqual(result["dossier"]["decision_price"], Decimal("12.36"))
        self.assertEqual(result["dossier"]["market"]["minimum_price"], Decimal("9.84"))
        self.assertEqual(result["dossier"]["market"]["median_price"], Decimal("12.40"))
        self.assertEqual(result["dossier"]["market"]["maximum_price"], Decimal("34.99"))
        self.assertEqual(result["cost_analysis"]["projected_margin_rate"], Decimal("10.00"))
