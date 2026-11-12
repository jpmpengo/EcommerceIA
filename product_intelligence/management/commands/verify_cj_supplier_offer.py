import os
import ssl

import httpx
import truststore
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from product_intelligence.models import SupplierOffer
from product_intelligence.services.cj_auth_client import CJAuthClient
from product_intelligence.services.cj_client import CJClient
from product_intelligence.services.variant_features import VariantFeaturesService


class Command(BaseCommand):
    help = "Vérifie et complète une offre CJ sans créer de commande fournisseur."

    def add_arguments(self, parser):
        parser.add_argument("supplier_offer_id", type=int)

    def handle(self, *args, **options):
        api_key = os.getenv("CJ_API_KEY")
        if not api_key:
            raise CommandError("CJ_API_KEY is missing.")

        offer = SupplierOffer.objects.select_related("supplier").get(
            id=options["supplier_offer_id"]
        )
        if offer.supplier.name.lower() != "cjdropshipping":
            raise CommandError("Cette offre n'appartient pas à CJdropshipping.")
        if not offer.supplier_product_id:
            raise CommandError("L'identifiant de variante CJ est absent.")

        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=ssl_context, timeout=30.0) as http_client:
            token = CJAuthClient(api_key, http_client).get_access_token()
            client = CJClient(token, http_client)
            variant = client.get_variant_by_id(offer.supplier_product_id)
            stock = client.get_variant_stock(offer.supplier_product_id)

        if not variant:
            raise CommandError("CJ n'a retourné aucune variante.")
        if str(variant.get("vid")) != offer.supplier_product_id:
            raise CommandError("La variante CJ retournée ne correspond pas à l'offre.")

        features = VariantFeaturesService().extract(variant)
        offer.supplier_parent_product_id = str(variant.get("pid") or "")
        offer.supplier_sku = str(variant.get("variantSku") or "")
        offer.variant_features = {
            key: value for key, value in features.items() if value is not None
        }
        if variant.get("variantImage"):
            offer.image_url = variant["variantImage"]
        if stock is not None:
            offer.stock = stock
        offer.supplier_verified_at = timezone.now()
        offer.save(update_fields=[
            "supplier_parent_product_id",
            "supplier_sku",
            "variant_features",
            "image_url",
            "stock",
            "supplier_verified_at",
        ])

        self.stdout.write(f"OFFRE: {offer.id}")
        self.stdout.write(f"VID: {offer.supplier_product_id}")
        self.stdout.write(f"PID: {offer.supplier_parent_product_id}")
        self.stdout.write(f"SKU: {offer.supplier_sku}")
        self.stdout.write(f"VARIANTE: {offer.variant_features}")
        self.stdout.write(f"PRIX API: {variant.get('variantSellPrice')} USD")
        self.stdout.write(f"STOCK: {offer.stock}")
        self.stdout.write(self.style.SUCCESS("OFFRE CJ VERIFIEE EN LECTURE SEULE"))
