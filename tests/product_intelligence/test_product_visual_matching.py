from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.product_visual_matching import (
    ProductVisualMatchingService,
)


class ProductVisualMatchingServiceTests(SimpleTestCase):

    def test_matches_supplier_offers_against_retail_references(self):
        client = Mock()
        client.match.return_value = {
            "matches": [
                {
                    "offer_id": 296,
                    "visual_score": 25,
                    "same_product_probability": 5,
                    "classification": "rejected",
                    "evidence": "Phare avant seul.",
                    "differences": [
                        "Aucun feu arriere visible.",
                    ],
                },
            ],
        }

        service = ProductVisualMatchingService(
            client=client,
        )

        references = [
            {
                "product_name": "Kit eclairage 350 lm",
                "image_url": "https://example.com/reference.jpg",
            },
            {
                "product_name": "Reference sans image",
                "image_url": "",
            },
        ]

        supplier_offers = [
            Mock(
                id=296,
                product_name="Bicycle front light",
                image_url="https://example.com/cj-296.jpg",
            ),
            Mock(
                id=297,
                product_name="Produit sans image",
                image_url="",
            ),
        ]

        result = service.match(
            references=references,
            supplier_offers=supplier_offers,
        )

        client.match.assert_called_once_with(
            references=[
                {
                    "product_name": "Kit eclairage 350 lm",
                    "image_url": "https://example.com/reference.jpg",
                },
            ],
            candidates=[
                {
                    "offer_id": 296,
                    "product_name": "Bicycle front light",
                    "image_url": "https://example.com/cj-296.jpg",
                },
            ],
        )

        self.assertEqual(
            result["matches"][0]["classification"],
            "rejected",
        )

