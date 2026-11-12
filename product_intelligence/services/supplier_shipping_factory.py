from product_intelligence.services.aw_shipping_estimator import (
    AWShippingEstimator,
)
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
from product_intelligence.services.eprolo_client import EproloClient
from product_intelligence.services.eprolo_shipping_estimator import (
    EproloShippingEstimator,
)


class SupplierShippingFactory:

    @classmethod
    def build(
        cls,
        http_client,
        aw_api_token=None,
        cj_api_key=None,
        printful_api_token=None,
        eprolo_api_key=None,
        eprolo_api_secret=None,
        eprolo_api_base_url=None,
        maximum_shipping_days=20,
    ):
        estimators = []

        if aw_api_token:
            estimators.append(
                AWShippingEstimator()
            )

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
                    maximum_shipping_days=(
                        maximum_shipping_days
                    ),
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

        if eprolo_api_key and eprolo_api_secret:
            eprolo_client = EproloClient(
                api_key=eprolo_api_key,
                api_secret=eprolo_api_secret,
                http_client=http_client,
                base_url=eprolo_api_base_url,
            )
            estimators.append(
                EproloShippingEstimator(
                    client=eprolo_client,
                    maximum_shipping_days=(
                        maximum_shipping_days
                    ),
                )
            )

        return MultiSupplierShippingService(
            estimators=estimators,
        )
