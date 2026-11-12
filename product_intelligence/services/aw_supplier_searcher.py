class AWSupplierSearcher:

    def __init__(
        self,
        client,
        supplier,
        offer_service,
        matching_service,
        max_offers=5,
    ):
        self.client = client
        self.supplier = supplier
        self.offer_service = offer_service
        self.matching_service = matching_service
        self.max_offers = max_offers

    def search_for_idea(self, product_idea):
        keywords = list(
            product_idea.supplier_search_keywords
            or [product_idea.name]
        )
        offers = []
        seen_products = set()
        seen_codes_with_ean = set()
        searched_terms = set()

        for keyword in keywords:
            if len(offers) >= self.max_offers:
                break

            if keyword in searched_terms:
                continue
            searched_terms.add(keyword)
            products = self.client.search_products(keyword)
            used_fallback = False

            if not products:
                short_keyword = keyword.split()[-1] if keyword.split() else keyword
                if short_keyword != keyword and short_keyword not in searched_terms:
                    searched_terms.add(short_keyword)
                    products = self.client.search_products(short_keyword)
                    used_fallback = True

            products = sorted(products, key=lambda p: (not bool(p.get("ean_barcode")), str(p.get("code") or ""), str(p.get("id") or "")))

            for product in products:
                if len(offers) >= self.max_offers:
                    break

                product_id = product.get("id")
                ean = product.get("ean_barcode")

                if not product_id:
                    continue

                product_name = product.get("name") or ""
                if used_fallback:
                    is_relevant = any(
                        self.matching_service.is_relevant(
                            product_name,
                            supplier_keyword,
                        )
                        for supplier_keyword in keywords
                    )
                else:
                    is_relevant = self.matching_service.is_relevant(
                        product_name,
                        keyword,
                    )

                if not is_relevant:
                    continue

                canonical_product = product
                code = product.get("code")
                if code:
                    exact_products = self.client.search_products(code)
                    for exact_product in exact_products:
                        exact_ean = exact_product.get("ean_barcode")
                        if (
                            ean
                            and exact_ean
                            and str(exact_ean) == str(ean)
                        ):
                            canonical_product = exact_product
                            break

                canonical_id = canonical_product.get("id")
                canonical_ean = canonical_product.get("ean_barcode")
                canonical_code = canonical_product.get("code")

                if (
                    canonical_code
                    and not canonical_ean
                    and canonical_code in seen_codes_with_ean
                ):
                    continue

                identity = (
                    ("ean", str(canonical_ean))
                    if canonical_ean
                    else ("id", str(canonical_id))
                )

                if identity in seen_products:
                    continue

                offer = self.offer_service.create_offer(
                    supplier=self.supplier,
                    product=canonical_product,
                    product_idea=product_idea,
                    supplier_search_keyword=keyword,
                )
                offers.append(offer)
                seen_products.add(identity)
                if canonical_code and canonical_ean:
                    seen_codes_with_ean.add(canonical_code)

        return offers[:self.max_offers]
