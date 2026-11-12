from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.openai_visual_matching_client import (
    OpenAIVisualMatchingClient,
)


class OpenAIVisualMatchingClientTests(SimpleTestCase):

    def test_builds_multimodal_request_and_returns_matches(self):
        sdk = Mock()
        parsed = Mock()
        parsed.model_dump.return_value = {
            "matches": [
                {
                    "offer_id": 296,
                    "visual_score": 25,
                    "same_product_probability": 5,
                    "classification": "rejected",
                    "evidence": "Phare avant seul.",
                    "differences": ["Aucun feu arriere visible."],
                },
            ],
        }
        item = Mock()
        item.type = "output_text"
        item.parsed = parsed
        message = Mock()
        message.type = "message"
        message.content = [item]
        response = Mock()
        response.output = [message]
        sdk.responses.parse.return_value = response

        client = OpenAIVisualMatchingClient(
            client=sdk,
            model="gpt-5.6-luna",
        )

        result = client.match(
            product_idea_name="Tapis de marche compacts sans poignées pour bureau et télétravail",
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
                    "image_url": "https://example.com/candidate.jpg",
                },
            ],
        )

        self.assertIn("sans poignées", str(sdk.responses.parse.call_args.kwargs["input"]).lower())
        self.assertEqual(
            result["matches"][0]["offer_id"],
            296,
        )
        call = sdk.responses.parse.call_args.kwargs
        self.assertEqual(call["model"], "gpt-5.6-luna")
        self.assertEqual(call["input"][0]["role"], "user")
        content = call["input"][0]["content"]
        self.assertTrue(any(x.get("type") == "input_image" for x in content))
        prompt = next(x["text"] for x in content if x.get("type") == "input_text")
        self.assertIn("type de produit", prompt.lower())
        self.assertIn("repères visuels", prompt.lower())
        self.assertIn("ne rejette pas", prompt.lower())

