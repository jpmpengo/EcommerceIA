import os
import ssl
import httpx
import truststore
from openai import OpenAI
from product_intelligence.models import OpportunityAIRecommendation
from product_intelligence.services.openai_client import OpenAIClient

from django.core.management.base import BaseCommand
from pydantic import BaseModel, Field


class MerchantSummaryResponse(BaseModel):
    merchant_summary: str = Field(min_length=20)


class Command(BaseCommand):
    help = "Genere les syntheses commerciales des recommandations historiques"

    def handle(self, *args, **options):
        recommendation = OpportunityAIRecommendation.objects.filter(opportunity__status="review", decision__in=["recommend", "reject"], merchant_summary="").order_by("opportunity_id")
        for recommendation in recommendation:
            instructions = "Redige merchant_summary en francais, en 2 a 4 phrases. Respecte la decision existante. Explique les principaux avantages et risques commerciaux. Maximum 65 mots au total. Commence par Emma recommande ou Emma deconseille. Evite les listes et les details techniques. N invente aucune donnee. Ne recalcule aucun indicateur financier. Ne cite aucun pourcentage de marge ou de rendement issu de l analyse historique. Les indicateurs financiers valides sont affiches separement dans le Briefing. Ne confonds pas marge nette et rendement sur cout."
            context = dict(product=recommendation.opportunity.name, decision=recommendation.decision, existing_analysis=recommendation.summary)
            ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            http_client = httpx.Client(verify=ssl_context, timeout=180.0)
            ai_client = OpenAIClient(client=OpenAI(http_client=http_client), model=os.getenv("OPENAI_MODEL", "gpt-5-mini"))
            result = ai_client.generate(instructions=instructions, context=context, response_model=MerchantSummaryResponse)
            self.stdout.write(f"OPPORTUNITE {recommendation.opportunity_id} - {recommendation.decision}")
            self.stdout.write(result["merchant_summary"])
            recommendation.merchant_summary = result["merchant_summary"]
            recommendation.save(update_fields=["merchant_summary"])

