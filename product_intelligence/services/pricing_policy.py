from decimal import Decimal

MARKET_PRICE_REFERENCE = "median"
ALLOWED_MARKET_PRICE_REFERENCES = ("minimum", "median", "maximum")
LOW_COMPETITION_MULTIPLIER = Decimal("1.10")
MODERATE_COMPETITION_MULTIPLIER = Decimal("0.90")


def get_market_price_reference():
    if MARKET_PRICE_REFERENCE not in ALLOWED_MARKET_PRICE_REFERENCES:
        raise ValueError("Reference de prix du marche invalide.")
    return MARKET_PRICE_REFERENCE
