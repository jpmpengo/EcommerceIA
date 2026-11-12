from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.cj_supplier_searcher import (
    CJSupplierSearcher,
)


class CJSupplierSearcherTests(
    SimpleTestCase
):

    def test_searches_cj_variants_from_market_observation(
        self,
    ):
        observation = Mock()
        observation.name = "Wireless Charger"

        supplier = Mock()
        client = Mock()

        client.search_products.return_value = [
            {
                "id": "P1",
                "nameEn": "Wireless Charger",
            },
        ]

        client.get_product_detail.return_value = {
            "id": "P1",
            "nameEn": "Wireless Charger",
            "sellPrice": 4.50,
        }

        normalized_product = {
            "external_id": "P1",
            "name": "Wireless Charger",
            "currency": "USD",
            "purchase_price": 4.50,
        }

        client.normalize_product.return_value = (
            normalized_product
        )

        variant = {
            "vid": "V1",
            "pid": "P1",
            "variantNameEn": (
                "Wireless Charger Black"
            ),
            "variantSellPrice": 4.50,
        }

        client.get_product_variants.return_value = [
            variant,
        ]

        client.get_variant_stock.return_value = 100

        expected_offer = Mock()
        offer_service = Mock()

        offer_service.create_offer_from_variant.return_value = (
            expected_offer
        )

        searcher = CJSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=offer_service,
            max_offers=3,
        )

        offers = searcher.search_offers(
            market_observation=observation,
        )

        client.search_products.assert_called_once_with(
            keyword="Wireless Charger",
        )

        client.get_product_detail.assert_called_once_with(
            product_id="P1",
        )

        client.normalize_product.assert_called_once_with(
            client.get_product_detail.return_value,
        )

        client.get_product_variants.assert_called_once_with(
            product_id="P1",
        )

        client.get_variant_stock.assert_called_once_with(
            variant_id="V1",
        )

        offer_service.create_offer_from_variant.assert_called_once_with(
            supplier=supplier,
            product=normalized_product,
            variant=variant,
            stock=100,
            supplier_search_keyword="Wireless Charger",
            market_observation=observation,
        )

        self.assertEqual(
            offers,
            [
                expected_offer,
            ],
        )

    def test_searches_cj_variants_from_product_idea(
        self,
    ):
        idea = Mock()
        idea.name = (
            "Accessoires de bureau ergonomiques"
        )
        idea.supplier_search_keywords = [
            "ergonomic office accessories",
        ]

        supplier = Mock()
        client = Mock()

        client.search_products.return_value = [
            {
                "id": "P1",
                "nameEn": (
                    "Ergonomic Laptop Stand"
                ),
            },
        ]

        client.get_product_detail.return_value = {
            "id": "P1",
            "nameEn": (
                "Ergonomic Laptop Stand"
            ),
            "sellPrice": 8.50,
        }

        normalized_product = {
            "external_id": "P1",
            "name": (
                "Ergonomic Laptop Stand"
            ),
            "currency": "USD",
            "purchase_price": 8.50,
        }

        client.normalize_product.return_value = (
            normalized_product
        )

        variant = {
            "vid": "V1",
            "pid": "P1",
            "variantNameEn": (
                "Ergonomic Laptop Stand Black"
            ),
            "variantSellPrice": 8.50,
        }

        client.get_product_variants.return_value = [
            variant,
        ]

        client.get_variant_stock.return_value = 100

        expected_offer = Mock()
        offer_service = Mock()

        offer_service.create_offer_from_variant.return_value = (
            expected_offer
        )

        searcher = CJSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=offer_service,
            max_offers=1,
        )

        offers = searcher.search_for_idea(
            product_idea=idea,
        )

        client.search_products.assert_called_once_with(
            keyword=(
                "ergonomic office accessories"
            ),
            country_code="CN",
        )

        offer_service.create_offer_from_variant.assert_called_once_with(
            supplier=supplier,
            product=normalized_product,
            variant=variant,
            stock=100,
            supplier_search_keyword="ergonomic office accessories",
            product_idea=idea,
            stock_country="CN",
        )

        self.assertEqual(
            offers,
            [
                expected_offer,
            ],
        )

    def test_rejects_unrelated_cj_product_for_idea(
        self,
    ):
        idea = Mock()
        idea.name = (
            "Rangements modulaires"
        )
        idea.supplier_search_keywords = [
            "space saving storage organizer",
        ]

        client = Mock()

        client.search_products.return_value = [
            {
                "id": "P1",
            },
        ]

        client.get_product_detail.return_value = {
            "id": "P1",
        }

        client.normalize_product.return_value = {
            "external_id": "P1",
            "name": (
                "Fake Hair Canvas Head Mold"
            ),
            "currency": "USD",
        }

        category_matching_service = Mock()

        category_matching_service.is_relevant.return_value = (
            False
        )

        offer_service = Mock()

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=offer_service,
            category_matching_service=(
                category_matching_service
            ),
        )

        offers = searcher.search_for_idea(
            product_idea=idea,
        )

        self.assertEqual(
            category_matching_service.is_relevant.call_count,
            1,
        )
        category_matching_service.is_relevant.assert_any_call(
            product_name=(
                "Fake Hair Canvas Head Mold"
            ),
            search_keyword=(
                "space saving storage organizer"
            ),
            alternative_keywords=[],
        )

        self.assertEqual(
            offers,
            [],
        )

        client.get_product_variants.assert_not_called()

        offer_service.create_offer_from_variant.assert_not_called()

    def test_keeps_only_one_variant_per_cj_product(
        self,
    ):
        idea = Mock()
        idea.name = "Rangements modulaires"
        idea.supplier_search_keywords = [
            "space saving storage organizer",
        ]

        client = Mock()

        client.search_products.return_value = [
            {
                "id": "P1",
            },
        ]

        client.get_product_detail.return_value = {
            "id": "P1",
        }

        product = {
            "external_id": "P1",
            "name": (
                "Space Saving Storage Organizer"
            ),
            "currency": "USD",
        }

        client.normalize_product.return_value = (
            product
        )

        first_variant = {
            "vid": "V1",
            "variantNameEn": (
                "Storage Organizer Black"
            ),
            "variantSellPrice": "8.50",
        }

        second_variant = {
            "vid": "V2",
            "variantNameEn": (
                "Storage Organizer White"
            ),
            "variantSellPrice": "8.75",
        }

        client.get_product_variants.return_value = [
            first_variant,
            second_variant,
        ]

        client.get_variant_stock.return_value = 100

        expected_offer = Mock()
        offer_service = Mock()

        offer_service.create_offer_from_variant.return_value = (
            expected_offer
        )

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=offer_service,
        )

        offers = searcher.search_for_idea(
            product_idea=idea,
        )

        self.assertEqual(
            offers,
            [
                expected_offer,
            ],
        )

        offer_service.create_offer_from_variant.assert_called_once_with(
            supplier=searcher.supplier,
            product=product,
            variant=first_variant,
            stock=100,
            supplier_search_keyword="space saving storage organizer",
            stock_country="CN",
            product_idea=idea,
        )

        client.get_variant_stock.assert_called_once_with(
            variant_id="V1",
            country_code="CN",
        )

    def test_tries_next_supplier_keyword_when_first_returns_nothing(
        self,
    ):
        idea = Mock()
        idea.name = "Rangements modulaires"
        idea.supplier_search_keywords = [
            "space saving storage organizer",
            "stackable storage box",
        ]

        client = Mock()

        client.search_products.side_effect = [
            [],
            [
                {
                    "id": "P2",
                },
            ],
        ]

        client.get_product_detail.return_value = {
            "id": "P2",
        }

        product = {
            "external_id": "P2",
            "name": "Stackable Storage Box",
            "currency": "USD",
        }

        client.normalize_product.return_value = (
            product
        )

        variant = {
            "vid": "V2",
            "variantNameEn": (
                "Stackable Storage Box"
            ),
            "variantSellPrice": "6.50",
        }

        client.get_product_variants.return_value = [
            variant,
        ]

        client.get_variant_stock.return_value = 75

        expected_offer = Mock()
        offer_service = Mock()

        offer_service.create_offer_from_variant.return_value = (
            expected_offer
        )

        category_matching_service = Mock()
        category_matching_service.is_relevant.return_value = (
            True
        )

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=offer_service,
            max_offers=1,
            category_matching_service=(
                category_matching_service
            ),
        )

        offers = searcher.search_for_idea(
            product_idea=idea,
        )

        self.assertEqual(
            client.search_products.call_count,
            2,
        )

        client.search_products.assert_any_call(
            keyword=(
                "space saving storage organizer"
            ),
            country_code="CN",
        )

        client.search_products.assert_any_call(
            keyword="stackable storage box",
            country_code="CN",
        )

        self.assertEqual(
            offers,
            [
                expected_offer,
            ],
        )
    def test_product_idea_searches_china_directly(self):
        idea = Mock()
        idea.name = "Wireless mouse"
        idea.supplier_search_keywords = ["wireless mouse"]
        idea.supplier_search_keywords_localized = {}
        client = Mock()
        client.search_products.return_value = []
        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=Mock(),
            max_offers=5,
        )

        offers = searcher.search_for_idea(product_idea=idea)

        client.search_products.assert_called_once_with(
            keyword="wireless mouse",
            country_code="CN",
        )
        self.assertEqual(offers, [])

    def test_search_passes_country_code_to_cj_client(self):
        client = Mock()
        client.search_products.return_value = []

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=Mock(),
        )

        offers = searcher._search(
            keyword="wireless mouse",
            country_code="FR",
        )

        client.search_products.assert_called_once_with(
            keyword="wireless mouse",
            country_code="FR",
        )

        self.assertEqual(
            offers,
            [],
        )
    def legacy_test_product_idea_prefers_france_before_fallback(self):
        idea = Mock()
        idea.name = "Wireless mouse"
        idea.supplier_search_keywords = [
            "wireless mouse",
        ]

        client = Mock()
        client.search_products.return_value = [
            {
                "id": "P-FR",
            },
        ]
        client.get_product_detail.return_value = {
            "id": "P-FR",
        }
        product = {
            "external_id": "P-FR",
            "name": "Wireless Mouse",
            "currency": "USD",
        }
        client.normalize_product.return_value = product
        variant = {
            "vid": "V-FR",
            "variantNameEn": "Wireless Mouse",
            "variantSellPrice": "9.00",
        }
        client.get_product_variants.return_value = [variant]
        client.get_variant_stock.return_value = 20

        category_matching_service = Mock()
        category_matching_service.is_relevant.return_value = True

        expected_offer = Mock()
        offer_service = Mock()
        offer_service.create_offer_from_variant.return_value = (
            expected_offer
        )

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=offer_service,
            max_offers=1,
            category_matching_service=(
                category_matching_service
            ),
        )

        offers = searcher.search_for_idea(
            product_idea=idea,
        )

        client.search_products.assert_called_once_with(
            keyword="wireless mouse",
            country_code="FR",
        )
        self.assertEqual(
            offers,
            [expected_offer],
        )

    def legacy_test_product_idea_does_not_fall_back_to_cn_during_eu_search(self):
        idea = Mock()
        idea.name = "Wireless mouse"
        idea.supplier_search_keywords = ["wireless mouse"]

        client = Mock()
        client.search_products.return_value = []

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=Mock(),
            max_offers=1,
        )

        offers = searcher.search_for_idea(product_idea=idea)

        self.assertEqual(
            [call.kwargs["country_code"] for call in client.search_products.call_args_list],
            ["FR", "DE", "ES", "RO"],
        )
        self.assertEqual(offers, [])

    def legacy_test_product_idea_uses_localized_keyword_only_for_matching_in_germany(self):
        idea = Mock()
        idea.name = "Laptop accessories"
        idea.supplier_search_keywords = ["foldable laptop stand"]
        idea.supplier_search_keywords_localized = {
            "DE": {"foldable laptop stand": "Laptop Stander Faltbar"},
        }
        client = Mock()
        client.search_products.side_effect = [[], [{"id": "P-DE"}]]
        client.get_product_detail.return_value = {"id": "P-DE"}
        client.normalize_product.return_value = {
            "external_id": "P-DE",
            "name": "Laptop Stander Notebook Tisch Halter Faltbar",
            "currency": "USD",
        }
        client.get_product_variants.return_value = [{"vid": "V-DE"}]
        client.get_variant_stock.return_value = 5
        category_matching_service = Mock()
        category_matching_service.is_relevant.return_value = True
        offer_service = Mock()
        offer_service.create_offer_from_variant.return_value = Mock()
        searcher = CJSupplierSearcher(client=client,supplier=Mock(),offer_service=offer_service,max_offers=1,category_matching_service=category_matching_service)
        searcher.search_for_idea(product_idea=idea)
        self.assertEqual(client.search_products.call_args_list,[__import__("unittest").mock.call(keyword="foldable laptop stand",country_code="FR"),__import__("unittest").mock.call(keyword="foldable laptop stand",country_code="DE")])
        category_matching_service.is_relevant.assert_called_with(product_name="Laptop Stander Notebook Tisch Halter Faltbar",search_keyword="foldable laptop stand",alternative_keywords=["Laptop Stander Faltbar"])

    def test_product_idea_uses_localized_keyword_in_germany(self):
        idea = Mock()
        idea.name = "Laptop accessories"
        idea.supplier_search_keywords = ["foldable laptop stand"]
        idea.supplier_search_keywords_localized = {
            "DE": {"foldable laptop stand": "Laptop Stander Faltbar"},
        }
        client = Mock()
        client.search_products.return_value = []
        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=Mock(),
            max_offers=1,
        )
        searcher.search_for_idea(product_idea=idea)
        self.assertNotIn(
            __import__("unittest").mock.call(
                keyword="Laptop Stander Faltbar",
                country_code="DE",
            ),
            client.search_products.call_args_list,
        )


    def legacy_test_product_idea_tries_germany_after_france(self):
        idea = Mock()
        idea.name = "Wireless mouse"
        idea.supplier_search_keywords = ["wireless mouse"]

        client = Mock()
        client.search_products.side_effect = [
            [],
            [{"id": "P-DE"}],
        ]
        client.get_product_detail.return_value = {"id": "P-DE"}
        product = {
            "external_id": "P-DE",
            "name": "Wireless Mouse",
            "currency": "USD",
        }
        client.normalize_product.return_value = product
        variant = {
            "vid": "V-DE",
            "variantNameEn": "Wireless Mouse",
            "variantSellPrice": "9.00",
        }
        client.get_product_variants.return_value = [variant]
        client.get_variant_stock.return_value = 50

        category_matching_service = Mock()
        category_matching_service.is_relevant.return_value = True

        expected_offer = Mock()
        offer_service = Mock()
        offer_service.create_offer_from_variant.return_value = expected_offer

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=offer_service,
            max_offers=1,
            category_matching_service=category_matching_service,
        )

        offers = searcher.search_for_idea(product_idea=idea)

        self.assertEqual(
            client.search_products.call_args_list,
            [
                __import__("unittest").mock.call(
                    keyword="wireless mouse",
                    country_code="FR",
                ),
                __import__("unittest").mock.call(
                    keyword="wireless mouse",
                    country_code="DE",
                ),
            ],
        )
        self.assertEqual(offers, [expected_offer])

    def legacy_test_product_idea_tries_spain_after_germany(self):
        idea = Mock()
        idea.name = "Wireless mouse"
        idea.supplier_search_keywords = ["wireless mouse"]

        client = Mock()
        client.search_products.side_effect = [
            [],
            [],
            [{"id": "P-ES"}],
        ]
        client.get_product_detail.return_value = {"id": "P-ES"}
        product = {
            "external_id": "P-ES",
            "name": "Wireless Mouse",
            "currency": "USD",
        }
        client.normalize_product.return_value = product
        variant = {
            "vid": "V-ES",
            "variantNameEn": "Wireless Mouse",
            "variantSellPrice": "9.00",
        }
        client.get_product_variants.return_value = [variant]
        client.get_variant_stock.return_value = 50

        category_matching_service = Mock()
        category_matching_service.is_relevant.return_value = True

        expected_offer = Mock()
        offer_service = Mock()
        offer_service.create_offer_from_variant.return_value = expected_offer

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=offer_service,
            max_offers=1,
            category_matching_service=category_matching_service,
        )

        offers = searcher.search_for_idea(product_idea=idea)

        self.assertEqual(
            [call.kwargs["country_code"] for call in client.search_products.call_args_list],
            ["FR", "DE", "ES"],
        )
        self.assertEqual(offers, [expected_offer])

    def legacy_test_product_idea_tries_romania_after_spain(self):
        idea = Mock()
        idea.name = "Wireless mouse"
        idea.supplier_search_keywords = ["wireless mouse"]

        client = Mock()
        client.search_products.side_effect = [
            [],
            [],
            [],
            [{"id": "P-RO"}],
        ]
        client.get_product_detail.return_value = {"id": "P-RO"}
        product = {
            "external_id": "P-RO",
            "name": "Wireless Mouse",
            "currency": "USD",
        }
        client.normalize_product.return_value = product
        variant = {
            "vid": "V-RO",
            "variantNameEn": "Wireless Mouse",
            "variantSellPrice": "9.00",
        }
        client.get_product_variants.return_value = [variant]
        client.get_variant_stock.return_value = 50

        category_matching_service = Mock()
        category_matching_service.is_relevant.return_value = True

        expected_offer = Mock()
        offer_service = Mock()
        offer_service.create_offer_from_variant.return_value = expected_offer

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=offer_service,
            max_offers=1,
            category_matching_service=category_matching_service,
        )

        offers = searcher.search_for_idea(product_idea=idea)

        self.assertEqual(
            [call.kwargs["country_code"] for call in client.search_products.call_args_list],
            ["FR", "DE", "ES", "RO"],
        )
        self.assertEqual(offers, [expected_offer])

    def legacy_test_product_idea_collects_across_eu_countries_before_cn(self):
        idea = Mock()
        idea.name = "Wireless mouse"
        idea.supplier_search_keywords = ["wireless mouse"]

        client = Mock()
        client.search_products.side_effect = [
            [{"id": "P-FR"}],
            [{"id": "P-DE"}],
        ]
        client.get_product_detail.side_effect = [
            {"id": "P-FR"},
            {"id": "P-DE"},
        ]
        client.normalize_product.side_effect = [
            {"external_id": "P-FR", "name": "Wireless Mouse FR", "currency": "USD"},
            {"external_id": "P-DE", "name": "Wireless Mouse DE", "currency": "USD"},
        ]
        client.get_product_variants.side_effect = [
            [{"vid": "V-FR", "variantNameEn": "Wireless Mouse FR", "variantSellPrice": "9.00"}],
            [{"vid": "V-DE", "variantNameEn": "Wireless Mouse DE", "variantSellPrice": "10.00"}],
        ]
        client.get_variant_stock.return_value = 50

        category_matching_service = Mock()
        category_matching_service.is_relevant.return_value = True

        offer_fr = Mock()
        offer_de = Mock()
        offer_service = Mock()
        offer_service.create_offer_from_variant.side_effect = [offer_fr, offer_de]

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=offer_service,
            max_offers=2,
            category_matching_service=category_matching_service,
        )

        offers = searcher.search_for_idea(product_idea=idea)

        self.assertEqual(
            [call.kwargs["country_code"] for call in client.search_products.call_args_list],
            ["FR", "DE"],
        )
        self.assertEqual(offers, [offer_fr, offer_de])

    def test_waits_between_cj_product_searches(self):
        idea = Mock()
        idea.name = "Wireless mouse"
        idea.supplier_search_keywords = ["wireless mouse"]

        client = Mock()
        client.search_products.return_value = []
        sleep_func = Mock()

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=Mock(),
            max_offers=1,
            sleep_func=sleep_func,
            request_delay=1.3,
        )

        searcher.search_for_idea(product_idea=idea)

        self.assertEqual(
            client.search_products.call_count,
            1,
        )
        self.assertEqual(
            sleep_func.call_count,
            0,
        )
        sleep_func.assert_not_called()


    def test_cn_search_ignores_localized_supplier_keywords(self):
        idea = Mock()
        idea.name = "Laptop accessories"
        idea.supplier_search_keywords = ["foldable laptop stand"]
        idea.supplier_search_keywords_localized = {
            "DE": {"foldable laptop stand": "Laptop Stander Faltbar"},
            "FR": {"foldable laptop stand": "support ordinateur portable pliable"},
        }
        client = Mock()
        client.search_products.return_value = []
        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=Mock(),
            max_offers=5,
        )
        searcher.search_for_idea_in_country(
            product_idea=idea,
            country_code="CN",
        )
        client.search_products.assert_called_once_with(
            keyword="foldable laptop stand",
            country_code="CN",
        )


    def test_can_search_product_idea_directly_in_cn(self):
        idea = Mock()
        idea.name = "Bicycle accessories"
        idea.supplier_search_keywords = ["USB rechargeable bike light"]
        client = Mock()
        client.search_products.return_value = []
        searcher = CJSupplierSearcher(client=client, supplier=Mock(), offer_service=Mock(), max_offers=5)
        offers = searcher.search_for_idea_in_country(product_idea=idea, country_code="CN")
        client.search_products.assert_called_once_with(keyword="USB rechargeable bike light", country_code="CN")
        self.assertEqual(offers, [])

    def test_passes_supplier_search_keyword_to_offer_service(self):
        idea = Mock()
        idea.name = "Bicycle accessories"
        idea.supplier_search_keywords = ["USB rechargeable bike light"]

        client = Mock()
        client.search_products.return_value = [
            {"id": "P1"},
        ]
        client.get_product_detail.return_value = {
            "id": "P1",
        }
        client.normalize_product.return_value = {
            "external_id": "P1",
            "name": "USB Rechargeable Bike Light",
            "currency": "USD",
        }
        client.get_product_variants.return_value = [
            {
                "vid": "V1",
                "pid": "P1",
                "variantNameEn": "USB Rechargeable Bike Light",
                "variantSellPrice": "8.50",
            },
        ]
        client.get_variant_stock.return_value = 100

        offer_service = Mock()
        offer_service.create_offer_from_variant.return_value = Mock()

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=offer_service,
            max_offers=1,
        )

        searcher.search_for_idea_in_country(
            product_idea=idea,
            country_code="CN",
        )

        self.assertEqual(
            offer_service.create_offer_from_variant.call_args.kwargs[
                "supplier_search_keyword"
            ],
            "USB rechargeable bike light",
        )
