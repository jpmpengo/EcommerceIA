from product_intelligence.services.cj_auth_client import (
    CJAuthClient,
)
from product_intelligence.services.cj_client import (
    CJClient,
)
from product_intelligence.services.cj_shipping_estimator import (
    CJShippingEstimator,
)
from product_intelligence.services.multi_supplier_shipping import (
    MultiSupplierShippingService,
)
from product_intelligence.services.printful_client import (
    PrintfulClient,
)
from product_intelligence.services.printful_shipping_estimator import (
    PrintfulShippingEstimator,
)


class SupplierShippingFactory:

    @classmethod
    def build(
        cls,
        http_client,
        cj_api_key=None,
        printful_api_token=None,
    ):
        estimators = []

        if cj_api_key:
            access_token = (
                CJAuthClient(
                    api_key=cj_api_key,
                    http_client=http_client,
                )
                .get_access_token()
            )

            cj_client = CJClient(
                access_token=access_token,
                http_client=http_client,
            )

            estimators.append(
                CJShippingEstimator(
                    client=cj_client,
                )
            )

        if printful_api_token:
            printful_client = PrintfulClient(
                api_token=(
                    printful_api_token
                ),
                http_client=http_client,
            )

            estimators.append(
                PrintfulShippingEstimator(
                    client=printful_client,
                )
            )

        return MultiSupplierShippingService(
            estimators=estimators,
        )