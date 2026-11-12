import json
from typing import Literal

from pydantic import BaseModel, Field


class StudyBlocker(BaseModel):
    category: Literal["comparable_prices", "demand", "competition", "logistics", "other"] = "other"
    blocker: str
    research_action: str
    resolution_criterion: str


class OpportunityAIResponse(BaseModel):
    decision: Literal[
        "study",
        "recommend",
        "reject",
    ]

    summary: str
    merchant_summary: str = ""
    commercial_name: str = ""
    commercial_description: str = ""
    category_path: list[str] = Field(default_factory=list)
    category_reason: str = ""
    study_blockers: list[StudyBlocker] = []


class OpenAIClient:

    def __init__(
        self,
        client,
        model,
    ):
        self.client = client
        self.model = model

    def generate(
        self,
        instructions,
        context,
        response_model=OpportunityAIResponse,
        use_web_search=False,
    ):
        request_options = {
            "model": self.model,
            "instructions": instructions,
            "input": json.dumps(
                context,
                ensure_ascii=False,
                default=str,
            ),
            "text_format": response_model,
        }

        if use_web_search:
            request_options["tools"] = [
                {
                    "type": "web_search",
                },
            ]

            request_options["tool_choice"] = (
                "required"
            )

        response = self.client.responses.parse(
            **request_options
        )

        for output in response.output:
            if output.type != "message":
                continue

            for item in output.content:
                if item.type != "output_text":
                    continue

                if item.parsed is None:
                    continue

                return item.parsed.model_dump()

        raise ValueError(
            (
                "La réponse IA structurée "
                "est introuvable."
            )
        )