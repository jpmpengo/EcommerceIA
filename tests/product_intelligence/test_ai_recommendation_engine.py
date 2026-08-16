import os
import ssl
from decimal import Decimal

import httpx
import truststore
from openai import OpenAI

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from product_intelligence.services.ai_recommendation_engine import (
    AIRecommendationEngine,
)
from product_intelligence.services.openai_client import (
    OpenAIClient,
)
from product_intelligence.services.opportunity_recommendation_service import (
    OpportunityRecommendationService,
)


class Command(BaseCommand):
    help = (
        "Teste une recommandation réelle "
        "avec le moteur IA d'EcommerceIA."
    )

    def handle(self, *args, **options):
        if not os.getenv("OPENAI_API_KEY"):
            raise CommandError(
                "OPENAI_API_KEY n'est pas définie."
            )

        model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5-mini",
        )

        self.stdout.write(
            f"Modèle utilisé : {model}"
        )

        #
        # Utilisation du magasin de certificats Windows.
        #
        # Nécessaire sur notre environnement professionnel
        # où le trafic HTTPS est inspecté par Netskope.
        #
        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        http_client = httpx.Client(
            verify=ssl_context,
            timeout=30.0,
        )

        sdk_client = OpenAI(
            http_client=http_client,
        )

        ai_client = OpenAIClient(
            client=sdk_client,
            model=model,
        )

        engine = AIRecommendationEngine(
            client=ai_client
        )

        service = OpportunityRecommendationService(
            engine=engine
        )

        product_data = {
            "name": "Support ordinateur portable",
            "current_price": Decimal("17.50"),
            "currency": "EUR",
        }

        score_data = {
            "score": Decimal("62.06"),
            "reasons": [
                "Baisse de prix de 12.06 %",
            ],
        }

        self.stdout.write(
            "Envoi de l'opportunité au moteur IA..."
        )

        try:
            result = service.recommend(
                product_data=product_data,
                score_data=score_data,
            )

        except Exception as exc:
            raise CommandError(
                (
                    "Échec de l'appel IA : "
                    f"{type(exc).__name__} - {exc}"
                )
            ) from exc

        finally:
            http_client.close()

        self.stdout.write(
            self.style.SUCCESS(
                "Réponse IA reçue."
            )
        )

        self.stdout.write(
            f"Décision : {result['decision']}"
        )

        self.stdout.write(
            f"Résumé : {result['summary']}"
        )

        
        