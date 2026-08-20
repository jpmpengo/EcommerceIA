import re


class SupplierProductMatchingService:

    PRODUCT_TYPES = {
        "mouse_pad": (
            "mouse pad",
            "mouse mat",
            "desk mat",
        ),
        "ceramic_mug": (
            "ceramic mug",
            "coffee mug",
            "glossy mug",
        ),
        "tote_bag": (
            "tote bag",
            "cotton bag",
        ),
    }

    @staticmethod
    def _normalize_name(
        name,
    ):
        if not name:
            return ""

        normalized = name.lower()

        normalized = re.sub(
            r"[^a-z0-9]+",
            " ",
            normalized,
        )

        return " ".join(
            normalized.split()
        )

    def _product_type(
        self,
        name,
    ):
        normalized = self._normalize_name(
            name
        )

        for (
            product_family,
            product_types,
        ) in self.PRODUCT_TYPES.items():
            for product_type in product_types:
                if product_type in normalized:
                    return product_family

        return None

    @staticmethod
    def _normalize_dimensions(
        dimensions,
    ):
        if dimensions is None:
            return None

        try:
            if len(dimensions) != 2:
                return None
        except TypeError:
            return None

        first, second = dimensions

        try:
            if (
                first <= 0
                or second <= 0
            ):
                return None
        except TypeError:
            return None

        return tuple(
            sorted(
                (
                    first,
                    second,
                )
            )
        )

    def are_products_comparable(
        self,
        first_name,
        second_name,
        first_dimensions=None,
        second_dimensions=None,
        first_capacity_ml=None,
        second_capacity_ml=None,
    ):
        first_type = self._product_type(
            first_name
        )

        second_type = self._product_type(
            second_name
        )

        if (
            first_type is None
            or second_type is None
        ):
            return False

        if first_type != second_type:
            return False

        if (
            second_dimensions is not None
            and first_dimensions is None
        ):
            return False

        if (
            second_capacity_ml is not None
            and first_capacity_ml is None
        ):
            return False

        if (
            first_dimensions is not None
            and second_dimensions is not None
        ):
            normalized_first_dimensions = (
                self._normalize_dimensions(
                    first_dimensions
                )
            )

            normalized_second_dimensions = (
                self._normalize_dimensions(
                    second_dimensions
                )
            )

            if (
                normalized_first_dimensions
                is None
                or normalized_second_dimensions
                is None
            ):
                return False

            first_width, first_length = (
                normalized_first_dimensions
            )

            second_width, second_length = (
                normalized_second_dimensions
            )

            width_ratio = (
                min(
                    first_width,
                    second_width,
                )
                / max(
                    first_width,
                    second_width,
                )
            )

            length_ratio = (
                min(
                    first_length,
                    second_length,
                )
                / max(
                    first_length,
                    second_length,
                )
            )

            if (
                width_ratio < 0.80
                or length_ratio < 0.80
            ):
                return False

        if (
            first_capacity_ml is not None
            and second_capacity_ml is not None
        ):
            try:
                if (
                    first_capacity_ml <= 0
                    or second_capacity_ml <= 0
                ):
                    return False

                capacity_ratio = (
                    min(
                        first_capacity_ml,
                        second_capacity_ml,
                    )
                    / max(
                        first_capacity_ml,
                        second_capacity_ml,
                    )
                )
            except TypeError:
                return False

            if capacity_ratio < 0.80:
                return False

        return True

        # Si aucune dimension n'est fournie
        # pour l'un des produits, on reste
        # sur la comparaison de famille.
        if (
            first_dimensions is None
            or second_dimensions is None
        ):
            return True

        # Si des dimensions sont fournies,
        # elles doivent être valides.
        normalized_first_dimensions = (
            self._normalize_dimensions(
                first_dimensions
            )
        )

        normalized_second_dimensions = (
            self._normalize_dimensions(
                second_dimensions
            )
        )

        if (
            normalized_first_dimensions is None
            or normalized_second_dimensions is None
        ):
            return False

        first_width, first_length = (
            normalized_first_dimensions
        )

        second_width, second_length = (
            normalized_second_dimensions
        )

        width_ratio = (
            min(
                first_width,
                second_width,
            )
            / max(
                first_width,
                second_width,
            )
        )

        length_ratio = (
            min(
                first_length,
                second_length,
            )
            / max(
                first_length,
                second_length,
            )
        )

        return (
            width_ratio >= 0.80
            and length_ratio >= 0.80
        )
