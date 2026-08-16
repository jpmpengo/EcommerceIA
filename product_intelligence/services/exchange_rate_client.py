from decimal import Decimal


class ExchangeRateClient:

    BASE_URL = "https://open.er-api.com/v6/latest"

    def __init__(self, http_client):
        self.http_client = http_client

    def get_rate(
        self,
        from_currency,
        to_currency,
    ):
        if from_currency == to_currency:
            return Decimal("1")

        url = f"{self.BASE_URL}/{from_currency}"

        response = self.http_client.get(url)

        data = response.json()

        rate = data.get("rates", {}).get(
            to_currency
        )

        if rate is None:
            raise ValueError(
                f"Exchange rate {to_currency} "
                f"not found for {from_currency}."
            )

        return Decimal(str(rate))
        