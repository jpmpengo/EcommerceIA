from django.test import SimpleTestCase

from product_intelligence.services.product_idea_discovery import (
    DemandSignalAssessment,
    ProductIdea,
    ProductDiscoveryResponse,
    ProductIdeaDiscoveryService,
)

from pydantic import ValidationError


class FakeDiscoveryClient:

    def __init__(self):
        self.received_instructions = None
        self.received_context = None
        self.received_response_model = None

    def generate(
        self,
        instructions,
        context,
        response_model,
        use_web_search=False,
    ):
        self.received_instructions = (
            instructions
        )

        self.received_context = context

        self.received_response_model = (
            response_model
        )
        self.received_use_web_search = (
            use_web_search
        )

        return {
            "ideas": [
                {
                    "name": (
                        f"Produit test {index}"
                    ),
                    "customer_problem": (
                        "Problème client à vérifier."
                    ),
                    "target_customer": (
                        "Client européen."
                    ),
                    "reason_to_study": (
                        "Hypothèse commerciale "
                        "à valider."
                    ),
                    "countries": [
                        "FR",
                        "BE",
                        "ES",
                    ],
                    "search_keywords": [
                        "produit test",
                    ],
                }
                for index in range(
                    1,
                    6,
                )
            ],
        }


class ProductIdeaDiscoveryServiceTests(
    SimpleTestCase
):

    def test_requests_exactly_five_ideas_for_initial_markets(
        self,
    ):
        client = FakeDiscoveryClient()

        service = (
            ProductIdeaDiscoveryService(
                client=client
            )
        )

        result = service.discover()

        self.assertEqual(
            client.received_context[
                "maximum_ideas"
            ],
            5,
        )

        self.assertEqual(
            client.received_context[
                "target_countries"
            ],
            [
                "FR",
                "BE",
                "ES",
            ],
        )

        self.assertEqual(
            client.received_response_model,
            ProductDiscoveryResponse,
        )

        self.assertEqual(
            len(result["ideas"]),
            5,
        )

        self.assertIn(
            "catégories",
            client.received_instructions,
        )

        self.assertIn(
            "sources",
            client.received_instructions,
        )

        self.assertIn(
            "signaux de demande",
            client.received_instructions,
        )
        self.assertIn("category_path", client.received_instructions)
        self.assertIn("trois niveaux", client.received_instructions)

        self.assertIn(
            "images associées",
            client.received_instructions,
        )

        self.assertNotIn(
            "marketplace",
            (
                client.received_instructions
                .lower()
            ),
        )

        self.assertIn("direct", client.received_instructions)
        self.assertIn("trend", client.received_instructions)
        self.assertIn("need", client.received_instructions)
        self.assertIn("contextual", client.received_instructions)

        self.assertTrue(
            client.received_use_web_search
        )

    def test_objective_uses_demand_and_precursor_radar_not_promising_categories(self):
        client = FakeDiscoveryClient()
        service = ProductIdeaDiscoveryService(client=client)
        service.discover()
        objective = client.received_context["objective"].lower()
        self.assertIn("demande", objective)
        self.assertIn("précurseur", objective)
        self.assertNotIn("prometteuses", objective)

    def test_response_rejects_categories_without_supplier_keywords(
        self,
    ):
        categories = [
            {
                "name": (
                    f"Catégorie test {index}"
                ),
                "customer_problem": (
                    "Problème client."
                ),
                "target_customer": (
                    "Client européen."
                ),
                "reason_to_study": (
                    "Catégorie à vérifier."
                ),
                "countries": [
                    "FR",
                ],
                "search_keywords": [
                    "catégorie test",
                ],
                "demand_signals": [
                    "Signal documenté.",
                ],
                "evidence_sources": [
                    {
                        "title": (
                            "Source publique"
                        ),
                        "url": (
                            "https://example.com/"
                            "source"
                        ),
                        "evidence": (
                            "La source décrit "
                            "la demande."
                        ),
                    },
                ],
            }
            for index in range(
                1,
                6,
            )
        ]

        with self.assertRaises(
            ValidationError
        ):
            ProductDiscoveryResponse.model_validate(
                {
                    "ideas": categories,
                }
            )
    def test_instructions_request_localized_keywords_for_cj_europe(self):
        instructions = ProductIdeaDiscoveryService.INSTRUCTIONS
        self.assertIn("supplier_search_keywords_localized", instructions)
        self.assertIn("CJ Europe", instructions)
        self.assertIn("FR", instructions)
        self.assertIn("DE", instructions)
        self.assertIn("ES", instructions)
        self.assertIn("anglais", instructions.lower())

    def test_instructions_request_confirmed_demand_and_precursor_radar_before_selecting_five(self):
        instructions = ProductIdeaDiscoveryService.INSTRUCTIONS.lower()
        self.assertIn("demande confirmée", instructions)
        self.assertIn("radar précurseur", instructions)
        self.assertIn("avant de sélectionner", instructions)
        self.assertIn("sans quota géographique", instructions)
        self.assertIn("sans ordre géographique", instructions)
        self.assertIn("fr/be/es", instructions)

    def test_instructions_prefer_identified_countries_over_generic_international_market(self):
        instructions = ProductIdeaDiscoveryService.INSTRUCTIONS
        self.assertIn("pays réellement identifiables", instructions)
        self.assertIn("International uniquement", instructions)

    def test_instructions_require_at_least_one_precursor_signal_per_idea(self):
        instructions = ProductIdeaDiscoveryService.INSTRUCTIONS.lower()
        self.assertIn("au moins un signal precursor", instructions)

    def test_instructions_require_market_and_role_for_each_demand_signal(self):
        instructions = ProductIdeaDiscoveryService.INSTRUCTIONS.lower()
        self.assertIn("markets", instructions)
        self.assertIn("role", instructions)
        self.assertIn("target_market", instructions)
        self.assertIn("precursor", instructions)

    def test_instructions_request_strength_for_each_demand_signal(self):
        instructions = ProductIdeaDiscoveryService.INSTRUCTIONS
        self.assertIn("strength", instructions)
        self.assertIn("weak", instructions)
        self.assertIn("moderate", instructions)
        self.assertIn("strong", instructions)

    def test_instructions_request_measurable_evidence_for_each_demand_signal(self):
        instructions = ProductIdeaDiscoveryService.INSTRUCTIONS
        self.assertIn("metric", instructions)
        self.assertIn("value", instructions)
        self.assertIn("source_url", instructions)
        self.assertIn("observed_at", instructions)

    def test_response_accepts_geographic_demand_signal_assessment(self):
        data = {
            "name": "Support ergonomique pour ordinateur portable",
            "customer_problem": "Améliorer le confort de travail.",
            "target_customer": "Télétravailleurs.",
            "reason_to_study": "Signaux internationaux documentés.",
            "countries": ["FR"],
            "category_path": ["Informatique", "Accessoires", "Supports ordinateur"],
            "search_keywords": ["support ordinateur portable"],
            "supplier_search_keywords": ["foldable laptop stand"],
            "supplier_search_keywords_localized": [{"supplier_search_keyword": "foldable laptop stand", "FR": "support ordinateur portable pliable", "DE": "faltbarer laptopstander", "ES": "soporte plegable para portatil"}],
            "visual_references": [{"supplier_search_keyword": "foldable laptop stand", "product_name": "Laptop stand", "source_title": "Source", "source_url": "https://example.com/product", "image_url": "https://example.com/image.jpg"}],
            "demand_signals": ["Adoption documentée sur plusieurs marchés."],
            "demand_signal_assessments": [{"type": "trend", "markets": ["US", "JP"], "role": "precursor", "metric": "search_trend", "value": "documented growth", "source_url": "https://example.com/source", "observed_at": "2026-09-25", "strength": "moderate"}],
            "evidence_sources": [{"title": "Source", "url": "https://example.com/source", "evidence": "Evidence"}],
        }
        idea = ProductIdea.model_validate(data)
        assessment = idea.demand_signal_assessments[0]
        self.assertEqual(assessment.markets, ["US", "JP"])
        self.assertEqual(assessment.role, "precursor")

    def test_response_accepts_hierarchical_category_path(self):
        data = {
            "name": "Éclairage rechargeable pour vélo",
            "customer_problem": "Être visible à vélo.",
            "target_customer": "Cyclistes urbains.",
            "reason_to_study": "Besoin documenté.",
            "countries": ["FR"],
            "category_path": ["Sport", "Vélo", "Éclairage"],
            "search_keywords": ["éclairage vélo"],
            "supplier_search_keywords": ["USB rechargeable bike light"],
            "supplier_search_keywords_localized": [{"supplier_search_keyword": "USB rechargeable bike light", "FR": "eclairage velo rechargeable USB", "DE": "USB wiederaufladbares fahrradlicht", "ES": "luz de bicicleta recargable USB"}],
            "visual_references": [{"supplier_search_keyword": "USB rechargeable bike light", "product_name": "Bike light", "source_title": "Source", "source_url": "https://example.com/product", "image_url": "https://example.com/image.jpg"}],
            "demand_signals": ["Signal documenté"],
            "demand_signal_assessments": [{"type": "direct", "markets": ["FR"], "role": "target_market", "metric": "adoption", "value": "documented demand", "source_url": "https://example.com/source", "observed_at": "2026-09-25", "strength": "moderate"}, {"type": "trend", "markets": ["US"], "role": "precursor", "metric": "search_trend", "value": "documented precursor growth", "source_url": "https://example.com/precursor", "observed_at": "2026-09-25", "strength": "moderate"}],
            "evidence_sources": [{"title": "Source", "url": "https://example.com/source", "evidence": "Evidence"}],
        }
        idea = ProductIdea.model_validate(data)
        self.assertEqual(idea.category_path, ["Sport", "Vélo", "Éclairage"])

    def test_openai_schema_uses_structured_localized_supplier_keywords(self):
        schema = ProductDiscoveryResponse.model_json_schema()
        localized = schema["$defs"]["ProductIdea"]["properties"]["supplier_search_keywords_localized"]
        self.assertEqual(localized["type"], "array")
        self.assertIn("items", localized)
        self.assertNotIn("additionalProperties", localized)

    def test_openai_schema_requires_every_product_idea_property(self):
        schema = ProductDiscoveryResponse.model_json_schema()
        idea_schema = schema["$defs"]["ProductIdea"]
        self.assertEqual(
            set(idea_schema["properties"]),
            set(idea_schema["required"]),
        )

    def test_response_accepts_localized_supplier_search_keywords(self):
        data = {
            "name": "Support ordinateur portable pliable",
            "customer_problem": "Améliorer l ergonomie du poste de travail.",
            "target_customer": "Télétravailleurs.",
            "reason_to_study": "Besoin documenté.",
            "countries": ["FR", "ES"],
            "category_path": ["Informatique", "Ergonomie"],
            "search_keywords": ["support ordinateur portable"],
            "supplier_search_keywords": ["foldable laptop stand"],
            "supplier_search_keywords_localized": [
                {
                    "supplier_search_keyword": "foldable laptop stand",
                    "FR": "support ordinateur portable pliable",
                    "DE": "faltbarer laptopständer",
                    "ES": "soporte plegable para portátil",
                }
            ],
            "visual_references": [{"supplier_search_keyword": "foldable laptop stand", "product_name": "Laptop stand", "source_title": "Source", "source_url": "https://example.com/product", "image_url": "https://example.com/image.jpg"}],
            "demand_signals": ["Signal documenté"],
            "demand_signal_assessments": [{"type": "direct", "markets": ["FR"], "role": "target_market", "metric": "adoption", "value": "documented demand", "source_url": "https://example.com/source", "observed_at": "2026-09-25", "strength": "moderate"}, {"type": "trend", "markets": ["US"], "role": "precursor", "metric": "search_trend", "value": "documented precursor growth", "source_url": "https://example.com/precursor", "observed_at": "2026-09-25", "strength": "moderate"}],
            "evidence_sources": [{"title": "Source", "url": "https://example.com/source", "evidence": "Evidence"}],
        }
        idea = ProductIdea.model_validate(data)
        self.assertEqual(idea.supplier_search_keywords_localized[0].DE, "faltbarer laptopständer")

    def test_response_rejects_category_path_deeper_than_three_levels(self):
        with self.assertRaises(ValueError):
            ProductIdea.model_validate({
                "name": "Produit",
                "category_path": ["Maison", "Cuisine", "Rangement", "Sous-évier"],
                "customer_problem": "Problème",
                "target_customer": "Client",
                "reason_to_study": "Raison",
                "countries": ["FR"],
                "search_keywords": ["produit"],
                "supplier_search_keywords": ["product"],
                "supplier_search_keywords_localized": {"FR": {"product": "produit"}, "DE": {"product": "produkt"}, "ES": {"product": "producto"}},
                "visual_references": [{"supplier_search_keyword": "product", "product_name": "Product", "source_title": "Source", "source_url": "https://example.com/product", "image_url": "https://example.com/image.jpg"}],
                "demand_signals": ["Signal"],
                "demand_signal_assessments": [{"type": "direct", "markets": ["FR"], "role": "target_market", "metric": "adoption", "value": "documented demand", "source_url": "https://example.com/source", "observed_at": "2026-09-25", "strength": "moderate"}, {"type": "trend", "markets": ["US"], "role": "precursor", "metric": "search_trend", "value": "documented precursor growth", "source_url": "https://example.com/precursor", "observed_at": "2026-09-25", "strength": "moderate"}],
                "evidence_sources": [{"title": "Source", "url": "https://example.com/source", "evidence": "Evidence"}],
            })

    def test_response_accepts_structured_demand_signal_assessments(self):
        data = {
            "ideas": [
                {
                    "name": f"Idea {i}",
                    "category_path": ["Maison", "Organisation"],
                    "customer_problem": "Problem",
                    "target_customer": "Customer",
                    "reason_to_study": "Reason",
                    "countries": ["FR"],
                    "search_keywords": ["keyword"],
                    "supplier_search_keywords": ["supplier keyword"],
                    "supplier_search_keywords_localized": [{"supplier_search_keyword": "supplier keyword", "FR": "mot cle fournisseur", "DE": "lieferanten schlusselwort", "ES": "palabra clave proveedor"}],
                    "visual_references": [
                        {
                            "supplier_search_keyword": "supplier keyword",
                            "product_name": "Product",
                            "source_title": "Source",
                            "source_url": "https://example.com/product",
                            "image_url": "https://example.com/image.jpg",
                        }
                    ],
                    "demand_signals": ["Documented demand"],
                    "demand_signal_assessments": [
                        {"type": "direct", "markets": ["FR"], "role": "target_market", "metric": "adoption", "value": "documented demand", "source_url": "https://example.com/source", "observed_at": "2026-09-25", "strength": "moderate"}, {"type": "trend", "markets": ["US"], "role": "precursor", "metric": "search_trend", "value": "documented precursor growth", "source_url": "https://example.com/precursor", "observed_at": "2026-09-25", "strength": "moderate"},
                    ],
                    "evidence_sources": [
                        {
                            "title": "Source",
                            "url": "https://example.com/source",
                            "evidence": "Evidence",
                        }
                    ],
                }
                for i in range(5)
            ]
        }

        result = ProductDiscoveryResponse.model_validate(data)

        self.assertEqual(
            result.ideas[0].demand_signal_assessments[0].type,
            "direct",
        )

    def test_demand_signal_requires_iso_observed_at(self):
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            DemandSignalAssessment.model_validate({
                "type": "trend",
                "markets": ["US"],
                "role": "precursor",
                "strength": "strong",
                "metric": "search_trend",
                "value": "documented growth",
                "source_url": "https://example.com/source",
                "observed_at": "Rapport 2025",
            })

    def test_demand_signal_accepts_strength_classification(self):
        assessment = DemandSignalAssessment.model_validate({
            "type": "direct",
            "markets": ["US"],
            "role": "precursor",
            "metric": "sales",
            "value": "10000+ purchases",
            "source_url": "https://example.com/product",
            "observed_at": "2026-09-25",
            "strength": "strong",
        })

        self.assertEqual(assessment.strength, "strong")

    def test_demand_signal_can_expose_measurable_market_evidence(self):
        assessment = DemandSignalAssessment.model_validate({
            "type": "direct",
            "markets": ["US"],
            "role": "precursor",
            "metric": "sales",
            "value": "10000+ purchases",
            "source_url": "https://example.com/product",
            "observed_at": "2026-09-25",
            "strength": "moderate",
        })

        self.assertEqual(assessment.metric, "sales")
        self.assertEqual(assessment.value, "10000+ purchases")
        self.assertEqual(assessment.source_url, "https://example.com/product")
        self.assertEqual(assessment.observed_at.isoformat(), "2026-09-25")

    def test_response_rejects_unknown_demand_signal_type(self):
        with self.assertRaises(ValueError):
            DemandSignalAssessment.model_validate({"type": "unknown"})

    def test_response_exposes_visual_reference_for_supplier_keyword(self):
        data = {
            "ideas": [
                {
                    "name": f"Bike idea {i}",
                    "category_path": ["Sport", "Vélo"],
                    "customer_problem": "Visibility",
                    "target_customer": "Cyclists",
                    "reason_to_study": "Demand",
                    "countries": ["FR"],
                    "search_keywords": ["bike light"],
                    "supplier_search_keywords": ["USB rechargeable bike light"],
                    "supplier_search_keywords_localized": [{"supplier_search_keyword": "USB rechargeable bike light", "FR": "eclairage velo rechargeable USB", "DE": "USB wiederaufladbares fahrradlicht", "ES": "luz de bicicleta recargable USB"}],
                    "visual_references": [
                        {
                            "supplier_search_keyword": "USB rechargeable bike light",
                            "product_name": "Rechargeable bike light",
                            "source_title": "Retail reference",
                            "source_url": "https://example.com/product",
                            "image_url": "https://example.com/image.jpg",
                        }
                    ],
                    "demand_signals": ["Documented demand"],
                    "demand_signal_assessments": [{"type": "direct", "markets": ["FR"], "role": "target_market", "metric": "adoption", "value": "documented demand", "source_url": "https://example.com/source", "observed_at": "2026-09-25", "strength": "moderate"}, {"type": "trend", "markets": ["US"], "role": "precursor", "metric": "search_trend", "value": "documented precursor growth", "source_url": "https://example.com/precursor", "observed_at": "2026-09-25", "strength": "moderate"}],
                    "evidence_sources": [{"title": "Source", "url": "https://example.com/source", "evidence": "Evidence"}],
                }
                for i in range(5)
            ]
        }
        result = ProductDiscoveryResponse.model_validate(data)
        reference = result.ideas[0].visual_references[0]
        self.assertEqual(reference.supplier_search_keyword, "USB rechargeable bike light")
        self.assertEqual(reference.image_url, "https://example.com/image.jpg")

    def test_response_accepts_extra_visual_references_when_all_supplier_keywords_are_covered(self):
        data = {
            "name": "Bike light",
            "customer_problem": "Visibility",
            "target_customer": "Cyclists",
            "reason_to_study": "Demand",
            "countries": ["FR"],
            "category_path": ["Sport", "Velo"],
            "search_keywords": ["bike light"],
            "supplier_search_keywords": ["USB rechargeable bike light"],
            "supplier_search_keywords_localized": [{"supplier_search_keyword": "USB rechargeable bike light", "FR": "eclairage velo rechargeable USB", "DE": "USB wiederaufladbares fahrradlicht", "ES": "luz de bicicleta recargable USB"}],
            "visual_references": [
                {"supplier_search_keyword": "USB rechargeable bike light", "product_name": "Bike light", "source_title": "Source 1", "source_url": "https://example.com/product-1", "image_url": "https://example.com/image-1.jpg"},
                {"supplier_search_keyword": "extra reference", "product_name": "Extra", "source_title": "Source 2", "source_url": "https://example.com/product-2", "image_url": "https://example.com/image-2.jpg"},
            ],
            "demand_signals": ["Documented demand"],
            "demand_signal_assessments": [{"type": "direct", "markets": ["US"], "role": "precursor", "strength": "strong", "metric": "sales", "value": "documented purchases", "source_url": "https://example.com/source", "observed_at": "2026-09-25"}],
            "evidence_sources": [{"title": "Source", "url": "https://example.com/source", "evidence": "Evidence"}],
        }

        idea = ProductIdea.model_validate(data)
        self.assertEqual(len(idea.visual_references), 2)

    def test_response_rejects_idea_without_precursor_signal(self):
        data = {
            "name": "Produit local seulement",
            "customer_problem": "Probleme",
            "target_customer": "Client",
            "reason_to_study": "Raison",
            "countries": ["FR"],
            "category_path": ["Maison"],
            "search_keywords": ["produit"],
            "supplier_search_keywords": ["product"],
            "supplier_search_keywords_localized": [{"supplier_search_keyword": "product", "FR": "produit", "DE": "produkt", "ES": "producto"}],
            "visual_references": [{"supplier_search_keyword": "product", "product_name": "Product", "source_title": "Source", "source_url": "https://example.com/product", "image_url": "https://example.com/image.jpg"}],
            "demand_signals": ["Signal local"],
            "demand_signal_assessments": [{"type": "direct", "markets": ["FR"], "role": "target_market", "strength": "strong", "metric": "sales", "value": "documented sales", "source_url": "https://example.com/source", "observed_at": "2026-09-28"}],
            "evidence_sources": [{"title": "Source", "url": "https://example.com/source", "evidence": "Evidence"}],
        }

        with self.assertRaises(ValidationError):
            ProductIdea.model_validate(data)

    def test_response_rejects_supplier_keyword_without_visual_reference(self):
        data = {
            "ideas": [
                {
                    "name": f"Bike idea {i}",
                    "customer_problem": "Visibility",
                    "target_customer": "Cyclists",
                    "reason_to_study": "Demand",
                    "countries": ["FR"],
                    "category_path": ["Sport", "Vélo", "Sécurité"],
                    "search_keywords": ["bike light"],
                    "supplier_search_keywords": [
                        "USB rechargeable bike light",
                        "reflective cycling vest",
                    ],
                    "supplier_search_keywords_localized": [{"supplier_search_keyword": "USB rechargeable bike light", "FR": "eclairage velo rechargeable USB", "DE": "USB wiederaufladbares fahrradlicht", "ES": "luz de bicicleta recargable USB"}, {"supplier_search_keyword": "reflective cycling vest", "FR": "gilet cycliste reflechissant", "DE": "reflektierende fahrradweste", "ES": "chaleco reflectante ciclismo"}],
                    "visual_references": [
                        {
                            "supplier_search_keyword": "USB rechargeable bike light",
                            "product_name": "Rechargeable bike light",
                            "source_title": "Retail reference",
                            "source_url": "https://example.com/product",
                            "image_url": "https://example.com/image.jpg",
                        }
                    ],
                    "demand_signals": ["Documented demand"],
                    "demand_signal_assessments": [{"type": "direct", "markets": ["FR"], "role": "target_market", "metric": "adoption", "value": "documented demand", "source_url": "https://example.com/source", "observed_at": "2026-09-25", "strength": "moderate"}, {"type": "trend", "markets": ["US"], "role": "precursor", "metric": "search_trend", "value": "documented precursor growth", "source_url": "https://example.com/precursor", "observed_at": "2026-09-25", "strength": "moderate"}],
                    "evidence_sources": [{"title": "Source", "url": "https://example.com/source", "evidence": "Evidence"}],
                }
                for i in range(5)
            ]
        }
        with self.assertRaises(ValidationError):
            ProductDiscoveryResponse.model_validate(data)

    def test_instructions_prioritize_us_jp_kr_without_exclusivity(self):
        instructions = ProductIdeaDiscoveryService.INSTRUCTIONS
        self.assertIn("US, JP et KR prioritaires", instructions)
        self.assertIn("autres marches autorises", instructions)
        self.assertIn("preuve d emergence recente", instructions)
        self.assertIn("differenciation sur FR/BE/ES", instructions)

    def test_rejects_weak_contextual_precursor(self):
        from unittest.mock import patch
        from pydantic import ValidationError
        data = {"type": "contextual", "markets": ["International"], "role": "precursor", "strength": "weak", "metric": "catalog_presence", "value": "Product exists", "source_url": "https://example.com", "observed_at": "2026-09-25"}
        assessment = DemandSignalAssessment.model_validate(data)
        self.assertEqual(assessment.strength, "weak")
        self.assertEqual(assessment.type, "contextual")

    def test_idea_rejects_only_weak_contextual_precursor(self):
        from unittest.mock import patch
        original = ProductIdea.model_validate
        def validate_with_weak_precursor(data):
            data = dict(data)
            data["demand_signal_assessments"] = [{"type": "contextual", "markets": ["International"], "role": "precursor", "strength": "weak", "metric": "catalog_presence", "value": "Product exists", "source_url": "https://example.com", "observed_at": "2026-09-25"}]
            with self.assertRaises(ValidationError):
                original(data)
        data = {"name": "Produit test", "category_path": ["Maison"], "customer_problem": "Besoin", "target_customer": "Client", "reason_to_study": "Etude", "countries": ["FR"], "search_keywords": ["produit"], "supplier_search_keywords": ["product"], "supplier_search_keywords_localized": [{"supplier_search_keyword": "product", "FR": "produit", "DE": "produkt", "ES": "producto"}], "visual_references": [{"supplier_search_keyword": "product", "product_name": "Product", "source_title": "Source", "source_url": "https://example.com/product", "image_url": "https://example.com/image.jpg"}], "demand_signals": ["Signal faible"], "evidence_sources": [{"title": "Source", "url": "https://example.com", "evidence": "Presence catalogue"}]}
        validate_with_weak_precursor(data)

    def test_demand_signal_rejects_invalid_source_url(self):
        data = {"type": "trend", "markets": ["US"], "role": "precursor", "strength": "strong", "metric": "search_trend", "value": "documented growth", "source_url": "not-a-valid-url", "observed_at": "2026-09-25"}
        with self.assertRaises(ValidationError):
            DemandSignalAssessment.model_validate(data)
