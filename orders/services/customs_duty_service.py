from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone


class CustomsDutyService:
    """Estime les droits UE sans inventer un taux tarifaire inconnu."""

    MONEY = Decimal("0.01")
    LOW_VALUE_LIMIT = Decimal("150.00")
    TEMPORARY_DUTY_START = date(2026, 7, 1)
    TEMPORARY_DUTY_END = date(2028, 7, 1)
    TEMPORARY_DUTY_PER_ITEM = Decimal("3.00")
    SOURCE_URL = (
        "https://taxation-customs.ec.europa.eu/news/"
        "guidance-and-legal-text-temporary-flat-fee-low-value-imports-"
        "which-will-apply-until-1-july-2028-2026-06-08_en"
    )
    EU_COUNTRIES = {
        "AT", "BE", "BG", "HR", "CY", "CZ", "DE", "DK", "EE", "ES",
        "FI", "FR", "GR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
        "NL", "PL", "PT", "RO", "SE", "SI", "SK",
    }

    def estimate(
        self,
        *,
        origin_country,
        destination_country,
        intrinsic_value,
        quantity,
        rule_date=None,
        excise_goods=False,
    ):
        origin = (origin_country or "").upper()
        destination = (destination_country or "").upper()
        applied_on = rule_date or timezone.localdate()

        if not origin or not destination:
            raise ValueError("L'origine et la destination douanières sont requises.")
        if destination not in self.EU_COUNTRIES:
            raise ValueError("La règle douanière actuelle couvre uniquement l'Union européenne.")
        if quantity <= 0:
            raise ValueError("La quantité douanière doit être positive.")
        if intrinsic_value < 0:
            raise ValueError("La valeur intrinsèque ne peut pas être négative.")
        if origin in self.EU_COUNTRIES:
            return self._result("intra_eu", Decimal("0"), applied_on)
        if excise_goods:
            raise ValueError("Les produits soumis à accise nécessitent une étude douanière.")
        if intrinsic_value > self.LOW_VALUE_LIMIT:
            raise ValueError(
                "Au-delà de 150 EUR, le code douanier et l'origine tarifaire sont requis."
            )
        if applied_on < self.TEMPORARY_DUTY_START:
            return self._result("low_value_exemption", Decimal("0"), applied_on)
        if applied_on < self.TEMPORARY_DUTY_END:
            amount = self.TEMPORARY_DUTY_PER_ITEM * Decimal(quantity)
            return self._result("eu_temporary_flat_fee", amount, applied_on)
        raise ValueError(
            "La règle temporaire de 3 EUR a expiré : une règle douanière à jour est requise."
        )

    def _result(self, method, amount, applied_on):
        return {
            "method": method,
            "amount": amount.quantize(self.MONEY, rounding=ROUND_HALF_UP),
            "unit_amount": (
                self.TEMPORARY_DUTY_PER_ITEM
                if method == "eu_temporary_flat_fee"
                else Decimal("0.00")
            ),
            "rule_date": applied_on,
            "source_url": self.SOURCE_URL,
        }
