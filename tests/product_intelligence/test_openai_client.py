from django.test import SimpleTestCase

from product_intelligence.services.openai_client import (
    OpenAIClient,
    OpportunityAIResponse,
)


class FakeParsedContent:

    type = "output_text"

    def __init__(self):
        self.parsed = OpportunityAIResponse(
            decision="study",
            summary="Opportunité à étudier.",
        )


class FakeMessageOutput:

    type = "message"

    def __init__(self):
        self.content = [
            FakeParsedContent(),
        ]


class FakeParsedResponse:

    def __init__(self):
        self.output = [
            FakeMessageOutput(),
        ]


class FakeResponsesAPI:

    def __init__(self):
        self.received_model = None
        self.received_instructions = None
        self.received_input = None
        self.received_text_format = None

    def parse(
        self,
        model,
        instructions,
        input,
        text_format,
    ):
        self.received_model = model
        self.received_instructions = instructions
        self.received_input = input
        self.received_text_format = text_format

        return FakeParsedResponse()


class FakeOpenAI:

    def __init__(self):
        self.responses = FakeResponsesAPI()


class OpenAIClientTests(SimpleTestCase):

    def test_generate_uses_structured_output(self):
        sdk_client = FakeOpenAI()

        client = OpenAIClient(
            client=sdk_client,
            model="test-model",
        )

        result = client.generate(
            instructions=(
                "Analyse cette opportunité."
            ),
            context={
                "product": {
                    "name": (
                        "Support ordinateur portable"
                    ),
                },
                "score": "62.06",
                "reasons": [
                    "Baisse de prix de 12.06 %",
                ],
            },
        )

        self.assertEqual(
            sdk_client.responses.received_model,
            "test-model",
        )

        self.assertEqual(
            sdk_client.responses.received_instructions,
            "Analyse cette opportunité.",
        )

        self.assertIsNotNone(
            sdk_client.responses.received_input,
        )

        self.assertEqual(
            sdk_client.responses.received_text_format,
            OpportunityAIResponse,
        )

        self.assertEqual(
            result,
            {
                "decision": "study",
                "summary": "Opportunité à étudier.",
            },
        )

        