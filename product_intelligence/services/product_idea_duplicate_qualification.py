from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, model_validator


class ProductIdeaDuplicateQualificationResponse(BaseModel):
    decision: Literal["duplicate", "distinct", "innovation"]
    justification: str
    functional_difference: str = ""
    evidence_url: str = ""

    @model_validator(mode="after")
    def validate_innovation(self):
        if self.decision == "innovation":
            if not self.functional_difference.strip() or not self.evidence_url.strip() or urlparse(self.evidence_url.strip()).scheme not in ("http", "https") or not urlparse(self.evidence_url.strip()).hostname:
                raise ValueError("Innovation sans amelioration fonctionnelle et source documentaire")
        return self


class ProductIdeaInnovationEvidenceResponse(BaseModel):
    is_supported: bool
    justification: str


class ProductIdeaDuplicateQualificationService:
    INSTRUCTIONS = (
        "Compare une nouvelle idee de produit avec une idee historique EcommerceIA. "
        "Decide duplicate si le produit et sa fonction principale sont equivalents sans amelioration fonctionnelle demontree. "
        "Decide distinct si les produits constituent des solutions concretement differentes, meme pour un besoin commun. "
        "Decide innovation uniquement si une amelioration fonctionnelle nouvelle, concrete et documentee distingue le candidat. "
        "Une nouvelle tendance, un concurrent ou un delai de livraison ne constitue pas une innovation fonctionnelle. "
        "Explique ta decision. Pour innovation, renseigne functional_difference et evidence_url. "
        "Ne considere pas une simple variation de nom, couleur, taille ou presentation comme une innovation."
    )

    def __init__(self, client):
        self.client = client

    EVIDENCE_INSTRUCTIONS = (
        "Verifie si le contenu documentaire fourni demontre explicitement une amelioration fonctionnelle concrete du nouveau produit par rapport au produit historique. "
        "Utilise exclusivement le contenu documentaire fourni. Ne suppose aucun fait absent de cette source. "
        "Une simple presence de mots-cles, une promesse commerciale vague, une nouvelle couleur, un changement de nom ou une tendance ne constituent pas une preuve. "
        "Reponds is_supported=true uniquement si la source decrit clairement la fonction annoncee et son application au produit propose. "
        "Sinon, reponds is_supported=false. Justifie precisement la decision."
    )

    def verify_innovation_evidence(self, idea, previous_idea, functional_difference, source_content):
        return self.client.generate(
            instructions=self.EVIDENCE_INSTRUCTIONS,
            context={"new_idea": idea, "historical_idea": previous_idea, "functional_difference": functional_difference, "source_content": source_content},
            response_model=ProductIdeaInnovationEvidenceResponse,
        )

    def qualify(self, idea, previous_idea):
        return self.client.generate(
            instructions=self.INSTRUCTIONS,
            context={"new_idea": idea, "historical_idea": previous_idea},
            response_model=ProductIdeaDuplicateQualificationResponse,
        )
