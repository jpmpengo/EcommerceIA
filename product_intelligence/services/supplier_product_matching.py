import re


class SupplierProductMatchingService:

    PRODUCT_TYPES = (
        "mouse pad",
        "mouse mat",
        "desk mat",
    )

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

        for product_type in self.PRODUCT_TYPES:
            if product_type in normalized:
                return "mouse_pad"

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

        
 