import os
import ssl

import httpx
import truststore

from django.core.management.base import BaseCommand, CommandError

from product_intelligence.services.cj_auth_client import CJAuthClient


class Command(BaseCommand):
    help = "Teste l'authentification réelle CJdropshipping."

    def handle(self, *args, **options):
        api_key = os.getenv("CJ_API_KEY")

        if not api_key:
            raise CommandError(
                "CJ_API_KEY is missing."
            )

        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        with httpx.Client(
            verify=ssl_context,
            timeout=30.0,
        ) as http_client:
            client = CJAuthClient(
                api_key=api_key,
                http_client=http_client,
            )

            token = client.get_access_token()

        if not token:
            raise CommandError(
                "CJ access token was not returned."
            )

        self.stdout.write(
            self.style.SUCCESS(
                "CJ authentication successful."
            )
        )

        