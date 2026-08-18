import re


class VariantFeaturesService:

    INCH_TO_MM = 25.4

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

        color = (
            variant.get("color")
            or self._extract_color(
                name
            )
        )

        return {
            "dimensions_mm": dimensions_mm,
            "color": color,
        }

    def _extract_dimensions_mm(
        self,
        value,
    ):
        if not value:
            return None

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
                float(inch_match.group(1))
                * self.INCH_TO_MM
            )

            second = (
                float(inch_match.group(2))
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
                float(cm_match.group(1))
                * 10
            )

            second = (
                float(cm_match.group(2))
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

        
