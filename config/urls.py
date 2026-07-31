from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("produits/", include("products.urls")),
    path("panier/", include("cart.urls")),
    path("commande/", include("orders.urls")),
    path("compte/", include("accounts.urls")),
    path("compte/", include("django.contrib.auth.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

