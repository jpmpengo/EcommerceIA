from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.aw_supplier_searcher import (
    AWSupplierSearcher,
)


class AWSupplierSearcherTests(SimpleTestCase):

    def test_searches_product_idea_keywords(self):
        idea = Mock()
        idea.name = "Jardinieres pour balcon"
        idea.supplier_search_keywords = [
            "balcony planter",
            "planter",
        ]

        supplier = Mock()
        client = Mock()
        matching = Mock()
        offer_service = Mock()

        expected_product = {
            "id": 188999,
            "code": "MacP-03",
            "name": "Macrame Pot Holder - Lrg Single Beaded",
            "ean_barcode": "5055796597338",
            "price": "10.96",
        }
        client.search_products.side_effect = [
            [],
            [expected_product],
            [expected_product],
        ]
        matching.is_relevant.return_value = True
        expected_offer = Mock()
        offer_service.create_offer.return_value = expected_offer

        searcher = AWSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=offer_service,
            matching_service=matching,
            max_offers=5,
        )

        offers = searcher.search_for_idea(idea)

        self.assertEqual(offers, [expected_offer])
        self.assertEqual(
            client.search_products.call_args_list[0].args[0],
            "balcony planter",
        )
        self.assertEqual(
            client.search_products.call_args_list[1].args[0],
            "planter",
        )
        offer_service.create_offer.assert_called_once_with(
            supplier=supplier,
            product=expected_product,
            product_idea=idea,
            supplier_search_keyword="balcony planter",
        )

    def test_rejects_unrelated_products(self):
        idea = Mock()
        idea.name = "Jardinieres pour balcon"
        idea.supplier_search_keywords = ["planter"]

        supplier = Mock()
        client = Mock()
        matching = Mock()
        offer_service = Mock()

        client.search_products.return_value = [
            {
                "id": 1,
                "name": "Unrelated decoration",
                "ean_barcode": "111",
                "price": "3.00",
            }
        ]
        matching.is_relevant.return_value = False

        searcher = AWSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=offer_service,
            matching_service=matching,
        )

        offers = searcher.search_for_idea(idea)

        self.assertEqual(offers, [])
        offer_service.create_offer.assert_not_called()

    def test_deduplicates_products_by_ean(self):
        idea = Mock()
        idea.name = "Jardinieres pour balcon"
        idea.supplier_search_keywords = ["planter"]

        supplier = Mock()
        client = Mock()
        matching = Mock()
        offer_service = Mock()

        client.search_products.return_value = [
            {
                "id": 188999,
                "name": "Macrame Pot Holder",
                "ean_barcode": "5055796597338",
                "price": "10.96",
            },
            {
                "id": 457709,
                "name": "Large Hanging Planter",
                "ean_barcode": "5055796597338",
                "price": "12.91",
            },
        ]
        matching.is_relevant.return_value = True
        expected_offer = Mock()
        offer_service.create_offer.return_value = expected_offer

        searcher = AWSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=offer_service,
            matching_service=matching,
        )

        offers = searcher.search_for_idea(idea)

        self.assertEqual(offers, [expected_offer])
        self.assertEqual(
            offer_service.create_offer.call_count,
            1,
        )

    def test_keeps_discovered_product_when_exact_code_ean_differs(self):
        idea = Mock()
        idea.name = "Jardinieres pour balcon"
        idea.supplier_search_keywords = ["planter"]
        supplier = Mock()
        client = Mock()
        matching = Mock()
        offer_service = Mock()
        discovered = {"id": 457709, "code": "MacP-03", "name": "Hanging Planter", "ean_barcode": "5055796597338", "price": "12.91"}
        different = {"id": 999999, "code": "MacP-03", "name": "Other Product", "ean_barcode": "9999999999999", "price": "1.00"}
        client.search_products.side_effect = [[discovered], [different]]
        matching.is_relevant.return_value = True
        expected_offer = Mock()
        offer_service.create_offer.return_value = expected_offer
        searcher = AWSupplierSearcher(client=client, supplier=supplier, offer_service=offer_service, matching_service=matching)
        offers = searcher.search_for_idea(idea)
        self.assertEqual(offers, [expected_offer])
        offer_service.create_offer.assert_called_once_with(supplier=supplier, product=discovered, product_idea=idea, supplier_search_keyword="planter")

    def test_resolves_discovered_product_to_exact_code_product(self):
        idea = Mock()
        idea.name = "Jardinieres pour balcon"
        idea.supplier_search_keywords = ["planter"]

        supplier = Mock()
        client = Mock()
        matching = Mock()
        offer_service = Mock()

        discovered_product = {
            "id": 457709,
            "code": "MacP-03",
            "name": "Large Single Beaded Macrame Hanging Planter - default",
            "ean_barcode": "5055796597338",
            "price": "12.91",
        }
        canonical_product = {
            "id": 188999,
            "code": "MacP-03",
            "name": "Macrame Pot Holder - Lrg Single Beaded",
            "ean_barcode": "5055796597338",
            "price": "10.96",
        }

        client.search_products.side_effect = [
            [discovered_product],
            [canonical_product],
        ]
        matching.is_relevant.return_value = True
        expected_offer = Mock()
        offer_service.create_offer.return_value = expected_offer

        searcher = AWSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=offer_service,
            matching_service=matching,
        )

        offers = searcher.search_for_idea(idea)

        self.assertEqual(offers, [expected_offer])
        self.assertEqual(
            [call.args[0] for call in client.search_products.call_args_list],
            ["planter", "MacP-03"],
        )
        offer_service.create_offer.assert_called_once_with(
            supplier=supplier,
            product=canonical_product,
            product_idea=idea,
            supplier_search_keyword="planter",
        )

    def test_uses_full_supplier_keywords_for_fallback_relevance(self):
        idea = Mock()
        idea.name = "Urban balcony gardening kits"
        idea.supplier_search_keywords = ["vertical balcony planter", "hanging railing planter"]
        supplier = Mock(); client = Mock(); matching = Mock(); offer_service = Mock()
        product = {"id": 457709, "name": "Large Macrame Hanging Planter", "ean_barcode": "5055796597338"}
        client.search_products.side_effect = [[], [product], []]
        matching.is_relevant.return_value = False
        searcher = AWSupplierSearcher(client=client, supplier=supplier, offer_service=offer_service, matching_service=matching)
        searcher.search_for_idea(idea)
        matching.is_relevant.assert_any_call(product["name"], "vertical balcony planter")
        matching.is_relevant.assert_any_call(product["name"], "hanging railing planter")

    def test_falls_back_to_short_aw_search_term(self):
        idea = Mock()
        idea.name = "Jardinieres pour balcon"
        idea.supplier_search_keywords = ["vertical balcony planter"]

        supplier = Mock()
        client = Mock()
        matching = Mock()
        offer_service = Mock()

        discovered = {
            "id": 457709,
            "code": "MacP-03",
            "name": "Large Single Beaded Macrame Hanging Planter - default",
            "ean_barcode": "5055796597338",
            "price": "12.91",
        }
        canonical = {
            "id": 188999,
            "code": "MacP-03",
            "name": "Macrame Pot Holder - Lrg Single Beaded",
            "ean_barcode": "5055796597338",
            "price": "10.96",
        }

        client.search_products.side_effect = [
            [],
            [discovered],
            [canonical],
        ]
        matching.is_relevant.return_value = True
        expected_offer = Mock()
        offer_service.create_offer.return_value = expected_offer

        searcher = AWSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=offer_service,
            matching_service=matching,
        )

        offers = searcher.search_for_idea(idea)

        self.assertEqual(offers, [expected_offer])
        self.assertEqual(
            [call.args[0] for call in client.search_products.call_args_list],
            ["vertical balcony planter", "planter", "MacP-03"],
        )
        matching.is_relevant.assert_called_with(
            discovered["name"],
            "vertical balcony planter",
        )
        offer_service.create_offer.assert_called_once_with(
            supplier=supplier,
            product=canonical,
            product_idea=idea,
            supplier_search_keyword="vertical balcony planter",
        )


    def test_prefers_ean_product_for_same_code(self):
        idea = Mock()
        idea.name = "Herb planter"
        idea.supplier_search_keywords = ["planter"]
        supplier = Mock()
        client = Mock()
        matching = Mock()
        offer_service = Mock()
        incomplete = {"id": 72142, "code": "FLV-06", "name": "Zinc Herb Planter", "ean_barcode": None, "price": "2.40"}
        complete = {"id": 71955, "code": "FLV-06", "name": "Zinc Herb Planter", "ean_barcode": "5055796557684", "price": "1.85"}
        client.search_products.return_value = [incomplete, complete]
        matching.is_relevant.return_value = True
        expected = Mock()
        offer_service.create_offer.return_value = expected
        searcher = AWSupplierSearcher(client=client, supplier=supplier, offer_service=offer_service, matching_service=matching, max_offers=1)
        offers = searcher.search_for_idea(idea)
        self.assertEqual(offers, [expected])
        offer_service.create_offer.assert_called_once_with(supplier=supplier, product=complete, product_idea=idea, supplier_search_keyword="planter")

    def test_skips_same_code_without_ean_after_ean_product(self):
        idea = Mock()
        idea.name = "Herb planter"
        idea.supplier_search_keywords = ["planter"]
        supplier = Mock()
        client = Mock()
        matching = Mock()
        offer_service = Mock()
        complete = {"id": 128167, "code": "FLV-06", "name": "Zinc Herb Planter", "ean_barcode": "5055796557684", "price": "2.40"}
        incomplete = {"id": 72142, "code": "FLV-06", "name": "Zinc Herb Planter", "ean_barcode": None, "price": "2.40"}
        client.search_products.return_value = [complete, incomplete]
        matching.is_relevant.return_value = True
        expected = Mock()
        offer_service.create_offer.return_value = expected
        searcher = AWSupplierSearcher(client=client, supplier=supplier, offer_service=offer_service, matching_service=matching)
        offers = searcher.search_for_idea(idea)
        self.assertEqual(offers, [expected])
        self.assertEqual(offer_service.create_offer.call_count, 1)
