from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch

from django.test import TestCase

from product_intelligence.models import (
    ProductIdea,
    ProductOpportunity,
    Supplier,
    SupplierOffer,
)
from product_intelligence.services.product_idea_manual_analysis import (
    ProductIdeaManualAnalysisService,
)


class ProductIdeaManualAnalysisServiceTests(TestCase):
    def setUp(self):
        self.idea = ProductIdea.objects.create(
            name="Produit de test",
            customer_problem="Problème client.",
            target_customer="Client cible.",
            reason_to_study="Raison de l’étude.",
            countries=["FR"],
            status="selected",
        )
        self.supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            supplier_type="dropshipper",
        )

    def make_offer(self, code, price, days):
        return SupplierOffer.objects.create(
            supplier=self.supplier,
            product_idea=self.idea,
            product_name=f"Produit {code}",
            purchase_price=Decimal(price),
            shipping_cost=Decimal("5.00"),
            shipping_days=days,
            shipping_country="FR",
            currency="EUR",
            supplier_product_id=code,
        )

    def viable_result(self, offer):
        return {
            "status": "ready_for_opportunity",
            "base_cost": {
                "base_cost": (
                    offer.purchase_price
                    + offer.shipping_cost
                ),
            },
            "cost_analysis": {
                "projected_profit": Decimal("2.00"),
            },
        }

    def run_service(self, analyzer):
        collector = Mock()
        collector.collect.return_value = {
            "offers_found": 2,
        }
        comparable_runner = Mock()
        comparable_runner.run.return_value = {
            "offers_processed": 2,
        }

        return ProductIdeaManualAnalysisService.run(
            product_idea=self.idea,
            candidate_collector=collector,
            comparable_runner=comparable_runner,
            analysis_runner=analyzer,
            economic_fallback=Mock(run=Mock(return_value=[])),
        )

    def test_prefers_profitable_offer_within_twenty_days(self):
        fast = self.make_offer("FAST", "8.00", 18)
        self.make_offer("FALLBACK", "1.00", 50)
        analyzer = Mock()

        def analyze(supplier_offer, create=False):
            if not create:
                return self.viable_result(supplier_offer)
            opportunity = ProductOpportunity.objects.create(
                name=supplier_offer.product_name,
                source_name=self.supplier.name,
                supplier_price=supplier_offer.purchase_price,
                market_price=Decimal("20.00"),
                supplier_offer=supplier_offer,
            )
            return {
                "status": "created",
                "opportunity": opportunity,
            }

        analyzer.process.side_effect = analyze
        result = self.run_service(analyzer)

        self.assertEqual(result["opportunities_created"], 1)
        self.assertEqual(
            ProductOpportunity.objects.get().supplier_offer,
            fast,
        )
        self.assertEqual(
            ProductOpportunity.objects.get().status,
            "review",
        )
        self.idea.refresh_from_db()
        self.assertEqual(self.idea.status, "validated")

    def test_uses_fifty_day_offer_when_no_priority_offer_exists(self):
        fallback = self.make_offer("FALLBACK", "3.00", 50)
        analyzer = Mock()

        def analyze(supplier_offer, create=False):
            if not create:
                return self.viable_result(supplier_offer)
            opportunity = ProductOpportunity.objects.create(
                name=supplier_offer.product_name,
                source_name=self.supplier.name,
                supplier_price=supplier_offer.purchase_price,
                market_price=Decimal("20.00"),
                supplier_offer=supplier_offer,
            )
            return {
                "status": "created",
                "opportunity": opportunity,
            }

        analyzer.process.side_effect = analyze
        result = self.run_service(analyzer)

        self.assertEqual(result["opportunities_created"], 1)
        self.assertEqual(
            ProductOpportunity.objects.get().supplier_offer,
            fallback,
        )

    def test_searches_cn_when_all_eu_offers_are_unprofitable(self):
        eu_offer = self.make_offer("EU", "20.00", 3)
        analyzer = Mock()

        def analyze(supplier_offer, create=False):
            if supplier_offer.pk == eu_offer.pk:
                return {
                    "status": "unprofitable",
                }
            return self.viable_result(supplier_offer)

        analyzer.process.side_effect = analyze

        collector = Mock()
        collector.collect.return_value = {
            "offers_found": 1,
        }

        comparable_runner = Mock()
        comparable_runner.run.return_value = {
            "offers_processed": 1,
        }

        economic_fallback = Mock()

        def create_cn_offer(product_idea):
            return [
                self.make_offer(
                    "CN-ECONOMIC-FALLBACK",
                    "8.00",
                    12,
                )
            ]

        economic_fallback.run.side_effect = create_cn_offer

        result = ProductIdeaManualAnalysisService.run(
            product_idea=self.idea,
            candidate_collector=collector,
            comparable_runner=comparable_runner,
            analysis_runner=analyzer,
            economic_fallback=economic_fallback,
        )

        economic_fallback.run.assert_called_once_with(
            product_idea=self.idea,
        )
        self.assertEqual(
            result["offers_unprofitable"],
            1,
        )

    def test_uses_default_economic_fallback_when_not_injected(self):
        self.make_offer("EU", "20.00", 3)
        analyzer = Mock()
        analyzer.process.return_value = {
            "status": "unprofitable",
        }
        collector = Mock()
        collector.collect.return_value = {
            "offers_found": 1,
        }
        comparable_runner = Mock()
        comparable_runner.run.return_value = {
            "offers_processed": 1,
        }
        economic_fallback = Mock()
        economic_fallback.run.return_value = []

        with patch(
            "product_intelligence.services.product_idea_manual_analysis.ComparablePriceRunnerFactory.build_economic_fallback",
            return_value=economic_fallback,
        ) as build_fallback:
            ProductIdeaManualAnalysisService.run(
                product_idea=self.idea,
                candidate_collector=collector,
                comparable_runner=comparable_runner,
                analysis_runner=analyzer,
            )

        build_fallback.assert_called_once_with()
        economic_fallback.run.assert_called_once_with(
            product_idea=self.idea,
        )

    def test_runs_economic_fallback_when_cn_offer_is_unprofitable(self):
        offer = self.make_offer("CN-ALREADY-TESTED", "8.00", 12)
        offer.stock_country = "CN"
        offer.save(update_fields=["stock_country"])

        analyzer = Mock()
        analyzer.process.return_value = {
            "status": "unprofitable",
        }

        collector = Mock()
        collector.collect.return_value = {
            "offers_found": 1,
        }

        comparable_runner = Mock()
        comparable_runner.run.return_value = {
            "offers_processed": 1,
        }

        economic_fallback = Mock()
        economic_fallback.run.return_value = []

        ProductIdeaManualAnalysisService.run(
            product_idea=self.idea,
            candidate_collector=collector,
            comparable_runner=comparable_runner,
            analysis_runner=analyzer,
            economic_fallback=economic_fallback,
        )

        economic_fallback.run.assert_called_once_with(product_idea=self.idea)

    def test_runs_cj_economic_fallback_when_other_supplier_is_viable(self):
        cj_offer = self.make_offer("CJ-EU", "20.00", 3)

        other_supplier = Supplier.objects.create(
            name="EPROLO",
            country="CN",
            supplier_type="dropshipper",
        )
        other_offer = SupplierOffer.objects.create(
            supplier=other_supplier,
            product_idea=self.idea,
            product_name="Produit EPROLO",
            purchase_price=Decimal("5.00"),
            shipping_cost=Decimal("5.00"),
            shipping_days=15,
            shipping_country="FR",
            currency="EUR",
            supplier_product_id="EPROLO-1",
        )

        analyzer = Mock()

        def analyze(supplier_offer, create=False):
            if supplier_offer.pk == cj_offer.pk:
                return {
                    "status": "unprofitable",
                }
            if supplier_offer.pk == other_offer.pk:
                return self.viable_result(supplier_offer)
            return self.viable_result(supplier_offer)

        analyzer.process.side_effect = analyze

        collector = Mock()
        collector.collect.return_value = {
            "offers_found": 2,
        }

        comparable_runner = Mock()
        comparable_runner.run.return_value = {
            "offers_processed": 2,
        }

        economic_fallback = Mock()
        economic_fallback.run.return_value = []

        ProductIdeaManualAnalysisService.run(
            product_idea=self.idea,
            candidate_collector=collector,
            comparable_runner=comparable_runner,
            analysis_runner=analyzer,
            economic_fallback=economic_fallback,
        )

        economic_fallback.run.assert_called_once_with(
            product_idea=self.idea,
        )

    def test_refuses_an_unselected_idea(self):
        self.idea.status = "proposed"
        self.idea.save(update_fields=["status"])

        with self.assertRaisesMessage(
            ValueError,
            "Seule une idée sélectionnée",
        ):
            ProductIdeaManualAnalysisService.run(
                product_idea=self.idea,
                candidate_collector=Mock(),
                comparable_runner=Mock(),
                analysis_runner=Mock(),
            )

    def test_allows_reanalysis_of_validated_idea(self):
        self.idea.status = "validated"
        self.idea.save(update_fields=["status"])
        analyzer = Mock()
        result = self.run_service(analyzer)
        self.assertEqual(result["product_idea_id"], self.idea.pk)
        self.idea.refresh_from_db()
        self.assertEqual(self.idea.status, "validated")

    def test_analyzes_only_offers_that_passed_visual_matching(self):
        accepted = self.make_offer("VISION-OK", "8.00", 12)
        rejected = self.make_offer("VISION-NO", "8.00", 12)
        unchecked = self.make_offer("VISION-EMPTY", "8.00", 12)

        accepted.visual_match_classification = "strong"
        accepted.save(update_fields=["visual_match_classification"])
        rejected.visual_match_classification = "rejected"
        rejected.save(update_fields=["visual_match_classification"])

        self.idea.visual_references.create(
            supplier_search_keyword="test keyword",
            product_name="Reference",
            image_url="https://example.com/reference.jpg",
        )

        analyzer = Mock()
        analyzer.process.return_value = {"status": "unprofitable"}

        result = self.run_service(analyzer)

        analyzed_ids = [
            call.kwargs["supplier_offer"].id
            for call in analyzer.process.call_args_list
            if call.kwargs.get("create") is False
        ]
        self.assertEqual(analyzed_ids, [accepted.id])
        self.assertEqual(result["offers_analyzed"], 1)

    def test_rejects_existing_review_opportunity_when_offer_becomes_unprofitable(self):
        offer = self.make_offer("STALE-REVIEW", "8.00", 12)
        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name=self.supplier.name,
            supplier_price=offer.purchase_price,
            market_price=Decimal("20.00"),
            supplier_offer=offer,
            status="review",
        )

        analyzer = Mock()
        analyzer.process.return_value = {
            "status": "unprofitable",
        }
        collector = Mock()
        collector.collect.return_value = {"offers_found": 1}
        comparable_runner = Mock()
        comparable_runner.run.return_value = {"offers_processed": 1}
        economic_fallback = Mock()
        economic_fallback.run.return_value = []

        ProductIdeaManualAnalysisService.run(
            product_idea=self.idea,
            candidate_collector=collector,
            comparable_runner=comparable_runner,
            analysis_runner=analyzer,
            economic_fallback=economic_fallback,
        )

        opportunity.refresh_from_db()
        self.assertEqual(opportunity.status, "rejected")
        self.assertTrue(ProductOpportunity.objects.filter(pk=opportunity.pk).exists())

    def test_rejects_existing_review_opportunity_when_offer_becomes_incomplete(self):
        offer = self.make_offer("STALE-INCOMPLETE", "8.00", 12)
        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name=self.supplier.name,
            supplier_price=offer.purchase_price,
            market_price=Decimal("20.00"),
            supplier_offer=offer,
            status="review",
        )

        analyzer = Mock()
        analyzer.process.return_value = {
            "status": "incomplete",
        }
        collector = Mock()
        collector.collect.return_value = {"offers_found": 1}
        comparable_runner = Mock()
        comparable_runner.run.return_value = {"offers_processed": 1}
        economic_fallback = Mock()
        economic_fallback.run.return_value = []

        ProductIdeaManualAnalysisService.run(
            product_idea=self.idea,
            candidate_collector=collector,
            comparable_runner=comparable_runner,
            analysis_runner=analyzer,
            economic_fallback=economic_fallback,
        )

        opportunity.refresh_from_db()
        self.assertEqual(opportunity.status, "rejected")
        self.assertTrue(ProductOpportunity.objects.filter(pk=opportunity.pk).exists())

    def test_refreshes_single_existing_review_opportunity_from_analysis_result(self):
        offer = self.make_offer("SINGLE-REFRESH", "8.00", 12)
        self.idea.demand_signal_assessments = [{"type": "direct"}]
        self.idea.save(update_fields=["demand_signal_assessments"])
        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name=self.supplier.name,
            supplier_price=Decimal("8.00"),
            shipping_cost=Decimal("5.00"),
            shipping_cost_is_known=True,
            other_costs=Decimal("2.00"),
            market_price=Decimal("20.00"),
            recommended_price=Decimal("20.00"),
            supplier_offer=offer,
            status="review",
            demand_score=0,
            competition_score=0,
            opportunity_score=80,
        )
        batch_id = uuid4()
        analysis_result = {
            "status": "ready_for_opportunity",
            "dossier": {
                "decision_price": Decimal("29.99"),
                "market": {
                    "collection_batch_id": batch_id,
                    "retained_count": 4,
                    "source_domain_count": 4,
                },
            },
            "base_cost": {
                "purchase_converted": Decimal("6.00"),
                "shipping_converted": Decimal("4.00"),
            },
            "cost_analysis": {
                "vat_amount": Decimal("5.00"),
                "import_duty": Decimal("3.00"),
                "payment_fee": Decimal("0.70"),
                "return_reserve": Decimal("1.50"),
                "safety_reserve": Decimal("0.50"),
            },
        }

        ProductIdeaManualAnalysisService.refresh_existing_review_opportunity(
            opportunity=opportunity,
            offer=offer,
            analysis_result=analysis_result,
        )

        opportunity.refresh_from_db()
        self.assertEqual(opportunity.market_collection_batch_id, batch_id)
        self.assertEqual(opportunity.market_price, Decimal("29.99"))
        self.assertEqual(opportunity.supplier_price, Decimal("6.00"))
        self.assertEqual(opportunity.shipping_cost, Decimal("4.00"))
        self.assertEqual(opportunity.demand_score, 100)
        self.assertEqual(opportunity.competition_score, 75)
        self.assertIsNone(opportunity.opportunity_score)

    def test_refreshes_competition_score_of_existing_review_opportunity(self):
        offer = self.make_offer("REFRESH-COMPETITION", "8.00", 12)
        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name=self.supplier.name,
            supplier_price=Decimal("8.00"),
            shipping_cost=Decimal("5.00"),
            shipping_cost_is_known=True,
            other_costs=Decimal("2.00"),
            market_price=Decimal("20.00"),
            recommended_price=Decimal("20.00"),
            supplier_offer=offer,
            status="review",
            competition_score=10,
        )

        analyzer = Mock()
        analyzer.process.return_value = {
            "status": "ready_for_opportunity",
            "dossier": {
                "decision_price": Decimal("29.99"),
                "market": {
                    "collection_batch_id": uuid4(),
                    "retained_count": 4,
                    "source_domain_count": 4,
                },
            },
            "base_cost": {
                "base_cost": Decimal("10.00"),
                "purchase_converted": Decimal("6.00"),
                "shipping_converted": Decimal("4.00"),
            },
            "cost_analysis": {
                "projected_profit": Decimal("8.00"),
                "vat_amount": Decimal("5.00"),
                "import_duty": Decimal("3.00"),
                "payment_fee": Decimal("0.70"),
                "return_reserve": Decimal("1.50"),
                "safety_reserve": Decimal("0.50"),
            },
        }

        ProductIdeaManualAnalysisService.run(
            product_idea=self.idea,
            candidate_collector=Mock(collect=Mock(return_value={"offers_found": 1})),
            comparable_runner=Mock(run=Mock(return_value={"offers_processed": 1})),
            analysis_runner=analyzer,
            economic_fallback=Mock(run=Mock(return_value=[])),
        )

        opportunity.refresh_from_db()
        self.assertEqual(opportunity.competition_score, 75)

    def test_refreshes_demand_score_of_existing_review_opportunity(self):
        offer = self.make_offer("REFRESH-DEMAND", "8.00", 12)
        self.idea.demand_signal_assessments = [
            {"type": "trend"},
            {"type": "need"},
        ]
        self.idea.save(update_fields=["demand_signal_assessments"])

        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name=self.supplier.name,
            supplier_price=Decimal("8.00"),
            shipping_cost=Decimal("5.00"),
            shipping_cost_is_known=True,
            other_costs=Decimal("2.00"),
            market_price=Decimal("20.00"),
            recommended_price=Decimal("20.00"),
            supplier_offer=offer,
            status="review",
            demand_score=10,
        )

        analyzer = Mock()
        analyzer.process.return_value = {
            "status": "ready_for_opportunity",
            "dossier": {
                "decision_price": Decimal("29.99"),
                "market": {"collection_batch_id": uuid4()},
            },
            "base_cost": {
                "base_cost": Decimal("10.00"),
                "purchase_converted": Decimal("6.00"),
                "shipping_converted": Decimal("4.00"),
            },
            "cost_analysis": {
                "projected_profit": Decimal("8.00"),
                "vat_amount": Decimal("5.00"),
                "import_duty": Decimal("3.00"),
                "payment_fee": Decimal("0.70"),
                "return_reserve": Decimal("1.50"),
                "safety_reserve": Decimal("0.50"),
            },
        }

        ProductIdeaManualAnalysisService.run(
            product_idea=self.idea,
            candidate_collector=Mock(collect=Mock(return_value={"offers_found": 1})),
            comparable_runner=Mock(run=Mock(return_value={"offers_processed": 1})),
            analysis_runner=analyzer,
            economic_fallback=Mock(run=Mock(return_value=[])),
        )

        opportunity.refresh_from_db()
        self.assertEqual(opportunity.demand_score, 87)

    def test_refreshes_opportunity_score_after_market_scores_change(self):
        offer = self.make_offer("REFRESH-SCORE", "8.00", 12)
        self.idea.demand_signal_assessments = [{"type": "direct"}]
        self.idea.save(update_fields=["demand_signal_assessments"])

        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name=self.supplier.name,
            supplier_price=Decimal("8.00"),
            shipping_cost=Decimal("5.00"),
            shipping_cost_is_known=True,
            other_costs=Decimal("2.00"),
            market_price=Decimal("20.00"),
            recommended_price=Decimal("20.00"),
            supplier_offer=offer,
            status="review",
            demand_score=0,
            competition_score=0,
            opportunity_score=0,
        )

        analyzer = Mock()
        analyzer.process.return_value = {
            "status": "ready_for_opportunity",
            "dossier": {
                "decision_price": Decimal("29.99"),
                "market": {
                    "collection_batch_id": uuid4(),
                    "retained_count": 3,
                    "source_domain_count": 3,
                },
            },
            "base_cost": {
                "base_cost": Decimal("10.00"),
                "purchase_converted": Decimal("6.00"),
                "shipping_converted": Decimal("4.00"),
            },
            "cost_analysis": {
                "projected_profit": Decimal("8.00"),
                "vat_amount": Decimal("5.00"),
                "import_duty": Decimal("3.00"),
                "payment_fee": Decimal("0.70"),
                "return_reserve": Decimal("1.50"),
                "safety_reserve": Decimal("0.50"),
            },
        }

        ProductIdeaManualAnalysisService.run(
            product_idea=self.idea,
            candidate_collector=Mock(collect=Mock(return_value={"offers_found": 1})),
            comparable_runner=Mock(run=Mock(return_value={"offers_processed": 1})),
            analysis_runner=analyzer,
            economic_fallback=Mock(run=Mock(return_value=[])),
        )

        opportunity.refresh_from_db()
        self.assertEqual(opportunity.demand_score, 100)
        self.assertEqual(opportunity.competition_score, 50)
        self.assertIsNone(opportunity.opportunity_score)

    def test_refreshes_financial_data_of_existing_review_opportunity(self):
        offer = self.make_offer("REFRESH-REVIEW", "8.00", 12)
        old_batch_id = uuid4()
        new_batch_id = uuid4()
        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name=self.supplier.name,
            supplier_price=Decimal("8.00"),
            shipping_cost=Decimal("5.00"),
            shipping_cost_is_known=True,
            other_costs=Decimal("2.00"),
            market_price=Decimal("20.00"),
            recommended_price=Decimal("20.00"),
            supplier_offer=offer,
            status="review",
            market_collection_batch_id=old_batch_id,
            opportunity_score=80,
        )

        analyzer = Mock()
        analyzer.process.return_value = {
            "status": "ready_for_opportunity",
            "dossier": {
                "decision_price": Decimal("29.99"),
                "market": {
                    "collection_batch_id": new_batch_id,
                },
            },
            "base_cost": {
                "base_cost": Decimal("10.00"),
                "purchase_converted": Decimal("6.00"),
                "shipping_converted": Decimal("4.00"),
            },
            "cost_analysis": {
                "projected_profit": Decimal("8.00"),
                "vat_amount": Decimal("5.00"),
                "import_duty": Decimal("3.00"),
                "payment_fee": Decimal("0.70"),
                "return_reserve": Decimal("1.50"),
                "safety_reserve": Decimal("0.50"),
            },
        }
        collector = Mock()
        collector.collect.return_value = {"offers_found": 1}
        comparable_runner = Mock()
        comparable_runner.run.return_value = {"offers_processed": 1}

        result = ProductIdeaManualAnalysisService.run(
            product_idea=self.idea,
            candidate_collector=collector,
            comparable_runner=comparable_runner,
            analysis_runner=analyzer,
            economic_fallback=Mock(run=Mock(return_value=[])),
        )

        opportunity.refresh_from_db()
        self.assertEqual(opportunity.status, "review")
        self.assertEqual(opportunity.market_price, Decimal("29.99"))
        self.assertEqual(opportunity.recommended_price, Decimal("29.99"))
        self.assertEqual(opportunity.supplier_price, Decimal("6.00"))
        self.assertEqual(opportunity.shipping_cost, Decimal("4.00"))
        self.assertEqual(opportunity.other_costs, Decimal("10.70"))
        self.assertEqual(opportunity.market_collection_batch_id, new_batch_id)
        self.assertIsNone(opportunity.opportunity_score)
        self.assertEqual(ProductOpportunity.objects.filter(supplier_offer=offer).count(), 1)
        self.assertEqual(result["opportunities_existing"], 1)

    def test_does_not_refresh_financial_data_of_existing_approved_opportunity(self):
        offer = self.make_offer("KEEP-APPROVED", "8.00", 12)
        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name=self.supplier.name,
            supplier_price=Decimal("8.00"),
            shipping_cost=Decimal("5.00"),
            shipping_cost_is_known=True,
            other_costs=Decimal("2.00"),
            market_price=Decimal("20.00"),
            recommended_price=Decimal("20.00"),
            supplier_offer=offer,
            status="approved",
        )

        analyzer = Mock()
        analyzer.process.return_value = {
            "status": "ready_for_opportunity",
            "dossier": {"decision_price": Decimal("29.99")},
            "base_cost": {
                "base_cost": Decimal("10.00"),
                "purchase_converted": Decimal("6.00"),
                "shipping_converted": Decimal("4.00"),
            },
            "cost_analysis": {
                "projected_profit": Decimal("8.00"),
                "vat_amount": Decimal("5.00"),
                "import_duty": Decimal("3.00"),
                "payment_fee": Decimal("0.70"),
                "return_reserve": Decimal("1.50"),
                "safety_reserve": Decimal("0.50"),
            },
        }
        collector = Mock()
        collector.collect.return_value = {"offers_found": 1}
        comparable_runner = Mock()
        comparable_runner.run.return_value = {"offers_processed": 1}

        ProductIdeaManualAnalysisService.run(
            product_idea=self.idea,
            candidate_collector=collector,
            comparable_runner=comparable_runner,
            analysis_runner=analyzer,
            economic_fallback=Mock(run=Mock(return_value=[])),
        )

        opportunity.refresh_from_db()
        self.assertEqual(opportunity.status, "approved")
        self.assertEqual(opportunity.market_price, Decimal("20.00"))
        self.assertEqual(opportunity.recommended_price, Decimal("20.00"))
        self.assertEqual(opportunity.supplier_price, Decimal("8.00"))
        self.assertEqual(opportunity.shipping_cost, Decimal("5.00"))
        self.assertEqual(opportunity.other_costs, Decimal("2.00"))

    def test_returns_approved_opportunity_to_review_when_offer_becomes_unprofitable(self):
        offer = self.make_offer("RECHECK-APPROVED", "8.00", 12)
        batch_id = uuid4()
        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name=self.supplier.name,
            supplier_price=offer.purchase_price,
            market_price=Decimal("20.00"),
            supplier_offer=offer,
            status="approved",
            market_collection_batch_id=batch_id,
        )

        analyzer = Mock()
        analyzer.process.return_value = {"status": "unprofitable"}
        collector = Mock()
        collector.collect.return_value = {"offers_found": 1}
        comparable_runner = Mock()
        comparable_runner.run.return_value = {"offers_processed": 1}
        economic_fallback = Mock()
        economic_fallback.run.return_value = []

        ProductIdeaManualAnalysisService.run(
            product_idea=self.idea,
            candidate_collector=collector,
            comparable_runner=comparable_runner,
            analysis_runner=analyzer,
            economic_fallback=economic_fallback,
        )

        opportunity.refresh_from_db()
        self.assertEqual(opportunity.status, "review")
        self.assertIsNone(opportunity.market_collection_batch_id)

    def test_returns_approved_opportunity_to_review_when_offer_becomes_incomplete(self):
        offer = self.make_offer("RECHECK-INCOMPLETE", "8.00", 12)
        batch_id = uuid4()
        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name=self.supplier.name,
            supplier_price=offer.purchase_price,
            market_price=Decimal("20.00"),
            supplier_offer=offer,
            status="approved",
            market_collection_batch_id=batch_id,
        )

        analyzer = Mock()
        analyzer.process.return_value = {"status": "incomplete"}
        collector = Mock()
        collector.collect.return_value = {"offers_found": 1}
        comparable_runner = Mock()
        comparable_runner.run.return_value = {"offers_processed": 1}
        economic_fallback = Mock()
        economic_fallback.run.return_value = []

        ProductIdeaManualAnalysisService.run(
            product_idea=self.idea,
            candidate_collector=collector,
            comparable_runner=comparable_runner,
            analysis_runner=analyzer,
            economic_fallback=economic_fallback,
        )

        opportunity.refresh_from_db()
        self.assertEqual(opportunity.status, "review")
        self.assertIsNone(opportunity.market_collection_batch_id)

    def test_rejects_idea_when_all_offers_are_customs_excluded(self):
        self.make_offer("CUSTOMS1", "160.00", 18)
        self.make_offer("CUSTOMS2", "180.00", 20)
        analyzer = Mock()
        analyzer.process.return_value = {"status": "customs_excluded"}
        result = self.run_service(analyzer)
        self.idea.refresh_from_db()
        self.assertEqual(self.idea.status, "rejected")
        self.assertEqual(result["reason"], "all_offers_customs_excluded")
        self.assertEqual(result["offers_customs_excluded"], 2)
        self.assertEqual(result["processed_opportunity_ids"], [])
        self.assertFalse(ProductOpportunity.objects.filter(supplier_offer__product_idea=self.idea).exists())
