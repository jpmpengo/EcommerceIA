from urllib.parse import (
    urlsplit,
    urlunsplit,
)


class ComparablePriceQualificationService:

    RETAINED_REASON = (
        "Données indispensables présentes."
    )

    @classmethod
    def qualify(
        cls,
        supplier_offer,
    ):
        examined = 0
        retained = 0
        rejected = 0
        observed_urls = set()

        comparable_prices = (
            supplier_offer
            .comparable_prices
            .order_by("id")
        )

        for comparable_price in comparable_prices:
            examined += 1

            rejection_reason = (
                cls._get_rejection_reason(
                    comparable_price
                )
            )

            if not rejection_reason:
                normalized_url = (
                    cls._normalize_source_url(
                        comparable_price.source_url
                    )
                )

                if normalized_url in observed_urls:
                    rejection_reason = (
                        "Source déjà observée."
                    )
                else:
                    observed_urls.add(
                        normalized_url
                    )

            if rejection_reason:
                comparable_price.qualification_status = (
                    "rejected"
                )

                comparable_price.qualification_reason = (
                    rejection_reason
                )

                rejected += 1
            else:
                comparable_price.qualification_status = (
                    "retained"
                )

                comparable_price.qualification_reason = (
                    cls.RETAINED_REASON
                )

                retained += 1

            comparable_price.save(
                update_fields=[
                    "qualification_status",
                    "qualification_reason",
                ]
            )

        return {
            "examined": examined,
            "retained": retained,
            "rejected": rejected,
        }

    @staticmethod
    def _get_rejection_reason(
        comparable_price,
    ):
        if comparable_price.observed_price <= 0:
            return "Prix non positif."

        if not comparable_price.product_name.strip():
            return "Nom du produit manquant."

        if not comparable_price.currency.strip():
            return "Devise manquante."

        if len(
            comparable_price.currency.strip()
        ) != 3:
            return "Code devise invalide."

        if not comparable_price.source_title.strip():
            return "Titre de source manquant."

        if not comparable_price.source_url.strip():
            return "URL de source manquante."

        if not comparable_price.evidence.strip():
            return "Preuve de comparabilité manquante."

        return ""

    @staticmethod
    def _normalize_source_url(
        source_url,
    ):
        parsed_url = urlsplit(
            source_url.strip()
        )

        normalized_path = (
            parsed_url.path.rstrip("/")
            or "/"
        )

        return urlunsplit(
            (
                parsed_url.scheme.lower(),
                parsed_url.netloc.lower(),
                normalized_path,
                "",
                "",
            )
        )