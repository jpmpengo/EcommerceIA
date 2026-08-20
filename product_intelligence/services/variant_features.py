import re

from html import unescape


class VariantFeaturesService:

    INCH_TO_MM = 25.4

    FL_OZ_TO_ML = 29.5735

    def extract(
        self,
        variant,
    ):
        name = (
            variant.get("name")
            or variant.get("variantNameEn")
            or ""
        )

        size = (
            variant.get("size")
            or name
        )

        dimensions_mm = (
            self._extract_dimensions_mm(
                size
            )
        )

        capacity_ml = (
            self._extract_capacity_ml(
                size
            )
        )

        color = (
            variant.get("color")
            or self._extract_color(
                name
            )
        )

        return {
            "dimensions_mm": dimensions_mm,
            "capacity_ml": capacity_ml,
            "color": color,
        }

    def _extract_dimensions_mm(
        self,
        value,
    ):
        if not value:
            return None

        value = unescape(
            str(value)
        )

        inch_match = re.search(
            r"(\d+(?:\.\d+)?)"
            r"\s*[″\"]"
            r"\s*[x×]\s*"
            r"(\d+(?:\.\d+)?)"
            r"\s*[″\"]",
            value,
        )

        if inch_match:
            first = (
                float(
                    inch_match.group(1)
                )
                * self.INCH_TO_MM
            )

            second = (
                float(
                    inch_match.group(2)
                )
                * self.INCH_TO_MM
            )

            return (
                int(round(first)),
                int(round(second)),
            )

        inch_unit_match = re.search(
            r"(\d+(?:\.\d+)?)"
            r"\s*[x×]\s*"
            r"(\d+(?:\.\d+)?)"
            r"\s*(?:in|inch|inches)\b",
            value,
            re.IGNORECASE,
        )

        if inch_unit_match:
            first = (
                float(
                    inch_unit_match.group(1)
                )
                * self.INCH_TO_MM
            )

            second = (
                float(
                    inch_unit_match.group(2)
                )
                * self.INCH_TO_MM
            )

            return (
                int(round(first)),
                int(round(second)),
            )

        cm_match = re.search(
            r"(\d+(?:\.\d+)?)"
            r"\s*[x×]\s*"
            r"(\d+(?:\.\d+)?)"
            r"(?:\s*[x×]\s*"
            r"\d+(?:\.\d+)?)?"
            r"\s*cm",
            value,
            re.IGNORECASE,
        )

        if cm_match:
            first = (
                float(
                    cm_match.group(1)
                )
                * 10
            )

            second = (
                float(
                    cm_match.group(2)
                )
                * 10
            )

            return (
                int(round(first)),
                int(round(second)),
            )

        mm_match = re.search(
            r"(\d+(?:\.\d+)?)"
            r"\s*[x×]\s*"
            r"(\d+(?:\.\d+)?)"
            r"(?:\s*[x×]\s*"
            r"\d+(?:\.\d+)?)?"
            r"\s*mm",
            value,
            re.IGNORECASE,
        )

        if mm_match:
            first = float(
                mm_match.group(1)
            )

            second = float(
                mm_match.group(2)
            )

            return (
                int(round(first)),
                int(round(second)),
            )

        return None

    def _extract_capacity_ml(
        self,
        value,
    ):
        if not value:
            return None

        value = unescape(
            str(value)
        )

        ml_match = re.search(
            r"(\d+(?:\.\d+)?)"
            r"\s*ml\b",
            value,
            re.IGNORECASE,
        )

        if ml_match:
            return int(
                round(
                    float(
                        ml_match.group(1)
                    )
                )
            )

        ounce_match = re.search(
            r"(\d+(?:\.\d+)?)"
            r"\s*(?:fl\s*)?oz\b",
            value,
            re.IGNORECASE,
        )

        if ounce_match:
            capacity = (
                float(
                    ounce_match.group(1)
                )
                * self.FL_OZ_TO_ML
            )

            return int(
                round(capacity)
            )

        return None

    @staticmethod
    def _extract_color(
        value,
    ):
        if not value:
            return None

        colors = (
            "Black",
            "White",
            "Grey",
            "Gray",
            "Red",
            "Blue",
            "Green",
            "Pink",
            "Rose Gold",
            "Silver",
        )

        lowered = value.lower()

        for color in colors:
            if color.lower() in lowered:
                return color

        return None
