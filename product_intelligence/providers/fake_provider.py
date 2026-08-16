class FakeProvider:

    def get_products(self):
        return [
            {
                "name": "Souris Logitech MX",
                "description": (
                    "Souris ergonomique sans fil."
                ),
                "supplier_price": 35,
                "market_price": 69,
                "shipping_cost": 5,
                "other_costs": 2,
                "demand_score": 85,
                "competition_score": 35,
                "initial_stock": 10,
            },
            {
                "name": "Clavier mécanique RGB",
                "description": (
                    "Clavier gaming mécanique."
                ),
                "supplier_price": 42,
                "market_price": 89,
                "shipping_cost": 6,
                "other_costs": 3,
                "demand_score": 90,
                "competition_score": 45,
                "initial_stock": 8,
            },
        ]
        