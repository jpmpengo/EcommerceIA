from typing import Literal

from pydantic import BaseModel, Field

from product_intelligence.services.visual_image_accessibility import VisualImageAccessibilityService


class VisualMatchResult(BaseModel):
    offer_id: int
    visual_score: int = Field(ge=0, le=100)
    same_product_probability: int = Field(ge=0, le=100)
    classification: Literal[
        "strong",
        "probable",
        "weak",
        "rejected",
    ]
    evidence: str
    differences: list[str] = Field(default_factory=list)


class VisualMatchingResponse(BaseModel):
    matches: list[VisualMatchResult] = Field(default_factory=list)


class OpenAIVisualMatchingClient:

    def __init__(
        self,
        client,
        model,
        image_detail="low",
    ):
        self.client = client
        self.model = model
        self.image_detail = image_detail

    def match(
        self,
        references,
        candidates,
        product_idea_name=None,
    ):
        content = [
            {
                "type": "input_text",
                "text": (
                    "Compare visuellement les références comme des repères visuels du type de produit recherché. Pour chaque candidat fournisseur, évalue s il appartient bien au même type de produit et remplit la même fonction générale que les références. Les références ne sont pas des modèles exacts à reproduire. Ne rejette pas un candidat uniquement à cause d une différence de marque, de couleur, de forme, de design ou de composition exacte du lot si le type de produit et la fonction restent conformes. Rejette uniquement lorsqu il s agit clairement d un autre type de produit, d une autre fonction ou d un accessoire non équivalent. Retourne un score visuel, une probabilité de correspondance de type, une classification strong/probable/weak/rejected, une justification factuelle et les différences visibles. N invente aucune caractéristique non visible."                ),
            },
        ]

        if product_idea_name:
            content.append({"type": "input_text", "text": "IDEE PRODUIT RECHERCHEE : " + product_idea_name + ". Tiens compte des caracteristiques explicitement demandees dans cette idee et signale toute incompatibilite visible avec un critere indispensable. Ne deduis pas une caracteristique invisible."})

        usable_references = 0
        usable_candidates = set()

        for reference in references:
            image_data = VisualImageAccessibilityService.fetch_image_data_url(reference["image_url"])
            if not image_data:
                continue
            usable_references += 1
            content.append({"type": "input_text", "text": "REFERENCE RETAIL - " + reference["product_name"]})
            content.append({"type": "input_image", "image_url": image_data, "detail": self.image_detail})

        for candidate in candidates:
            image_data = VisualImageAccessibilityService.fetch_image_data_url(candidate["image_url"])
            if not image_data:
                continue
            usable_candidates.add(candidate["offer_id"])
            content.append({"type": "input_text", "text": "CANDIDAT FOURNISSEUR " + str(candidate["offer_id"]) + " - " + candidate["product_name"]})
            content.append({"type": "input_image", "image_url": image_data, "detail": self.image_detail})

        if not usable_references or not usable_candidates:
            return {"matches": []}

        response = self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": content,
                },
            ],
            text_format=VisualMatchingResponse,
        )

        for output in response.output:
            if output.type != "message":
                continue

            for item in output.content:
                if item.type != "output_text":
                    continue

                if item.parsed is None:
                    continue

                result = item.parsed.model_dump()
                result["matches"] = [m for m in result.get("matches", []) if m.get("offer_id") in usable_candidates]
                return result

        raise ValueError(
            "La reponse visuelle structuree est introuvable."
        )
