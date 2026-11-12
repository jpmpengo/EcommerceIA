class ComparablePriceCollectionRunner:

    def __init__(
        self,
        research_pipeline,
        qualification_service=None,
        destination_country="FR",
        fallback_service=None,
        commercial_classification_service=None,
    ):
        self.research_pipeline = (
            research_pipeline
        )
        self.destination_country = (
            destination_country
        )
        self.qualification_service = (
            qualification_service
        )
        self.fallback_service = (
            fallback_service
        )
        self.commercial_classification_service = commercial_classification_service

    def run(
        self,
        product_idea,
    ):
        offers_processed = 0
        offers_researched = 0
        offers_incomplete = 0
        offers_rejected = 0
        offers_slow = 0
        offers_fallback = 0
        comparable_prices_saved = 0
        comparable_prices_examined = 0
        comparable_prices_retained = 0
        comparable_prices_rejected = 0

        has_visual_references = (
            product_idea.visual_references.exists()
        )

        all_supplier_offers = list(
            product_idea.supplier_offers.all()
        )

        for offer in all_supplier_offers:
            classification = getattr(
                offer,
                "visual_match_classification",
                "",
            )
            excluded_by_visual = (
                classification == "rejected"
                or (
                    has_visual_references
                    and not classification
                )
            )
            if excluded_by_visual:
                offer.comparable_prices.filter(
                    is_current=True,
                ).update(
                    is_current=False,
                )

        supplier_offers = [
            offer
            for offer in (
                all_supplier_offers
            )
            if (
                getattr(
                    offer,
                    "visual_match_classification",
                    "",
                ) != "rejected"
                and (
                    not has_visual_references
                    or bool(
                        getattr(
                            offer,
                            "visual_match_classification",
                            "",
                        )
                    )
                )
            )
        ]

        eu_offer_results = []

        for supplier_offer in supplier_offers:
            result = (
                self.research_pipeline.process(
                    supplier_offer=supplier_offer,
                    destination_country=(
                        self.destination_country
                    ),
                )
            )

            offers_processed += 1

            eu_offer_results.append(result)

            status = result.get("status")

            if status == "researched":
                offers_researched += 1

                if self.qualification_service is not None:
                    qualification = (
                        self.qualification_service.qualify(
                            supplier_offer
                        )
                    )
                    comparable_prices_examined += (
                        qualification["examined"]
                    )
                    comparable_prices_retained += (
                        qualification["retained"]
                    )
                    comparable_prices_rejected += (
                        qualification["rejected"]
                    )
                    if self.commercial_classification_service is not None:
                        comparables = list(supplier_offer.comparable_prices.filter(is_current=True, qualification_status="retained"))
                        if comparables:
                            self.commercial_classification_service.classify_and_save(supplier_offer, comparables)
            elif status == "rejected":
                offers_rejected += 1
            else:
                offers_incomplete += 1

            if (
                result.get("delivery_status")
                == "slow"
            ):
                offers_slow += 1

            if (
                result.get("delivery_status")
                == "fallback"
            ):
                offers_fallback += 1

            comparable_prices_saved += (
                result.get(
                    "comparable_prices_saved",
                    0,
                )
            )

        if self.fallback_service is not None:
            fallback_offers = self.fallback_service.run(
                product_idea=product_idea,
                eu_offer_results=eu_offer_results,
            )

            for supplier_offer in fallback_offers:
                result = self.research_pipeline.process(
                    supplier_offer=supplier_offer,
                    destination_country=self.destination_country,
                )

                offers_processed += 1
                status = result.get("status")

                if status == "researched":
                    offers_researched += 1
                    if self.qualification_service is not None:
                        qualification = self.qualification_service.qualify(
                            supplier_offer
                        )
                        comparable_prices_examined += qualification["examined"]
                        comparable_prices_retained += qualification["retained"]
                        comparable_prices_rejected += qualification["rejected"]
                elif status == "rejected":
                    offers_rejected += 1
                else:
                    offers_incomplete += 1

                if result.get("delivery_status") == "slow":
                    offers_slow += 1
                if result.get("delivery_status") == "fallback":
                    offers_fallback += 1

                comparable_prices_saved += result.get(
                    "comparable_prices_saved", 0
                )

        return {
            "offers_processed": (
                offers_processed
            ),
            "offers_researched": (
                offers_researched
            ),
            "offers_incomplete": (
                offers_incomplete
            ),
            "offers_rejected": (
                offers_rejected
            ),
            "offers_slow": offers_slow,
            "offers_fallback": offers_fallback,
            "comparable_prices_saved": (
                comparable_prices_saved
            ),
            "comparable_prices_examined": (
                comparable_prices_examined
            ),
            "comparable_prices_retained": (
                comparable_prices_retained
            ),
            "comparable_prices_rejected": (
                comparable_prices_rejected
            ),
        }
