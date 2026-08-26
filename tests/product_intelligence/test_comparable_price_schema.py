import json

from django.test import SimpleTestCase

from product_intelligence.services.comparable_price_search import (
    ComparablePriceSearchResponse,
)


class ComparablePriceSchemaTests(
    SimpleTestCase
):

    def test_schema_does_not_use_unsupported_regex_lookaround(
        self,
    ):
        schema = (
            ComparablePriceSearchResponse
            .model_json_schema()
        )

        serialized_schema = json.dumps(
            schema,
        )

        self.assertNotIn(
            "(?",
            serialized_schema,
        )