from decimal import Decimal, ROUND_HALF_UP


class CurrencyConversionService:

    def convert(
        self,
        amount,
        from_currency,
        to_currency,
        exchange_rate,
    ):
        if from_currency == to_currency:
            return amount

        converted = amount * exchange_rate

        return converted.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        