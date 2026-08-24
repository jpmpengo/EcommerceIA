from django.db import models
from django.utils import timezone

from .services.analyzer import OpportunityAnalyzer


class ProductOpportunity(models.Model):
    STATUS_CHOICES = [
        ("detected", "Détecté"),
        ("review", "À vérifier"),
        ("approved", "Approuvé"),
        ("published", "Publié"),
        ("restocked", "Réapprovisionné"),
        ("rejected", "Refusé"),
    ]

    name = models.CharField(
        max_length=255,
        verbose_name="Nom du produit",
    )

    source_name = models.CharField(
        max_length=100,
        verbose_name="Source",
    )

    source_url = models.URLField(
        blank=True,
        verbose_name="URL source",
    )

    supplier_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix fournisseur",
    )

    market_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix moyen du marché",
    )

    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Frais de livraison",
    )

    shipping_cost_is_known = models.BooleanField(
        default=False,
        verbose_name=(
            "Frais de livraison vérifiés"
        ),
    )

    other_costs = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Autres frais",
    )

    demand_score = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Score de demande",
    )

    competition_score = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Score de concurrence",
    )

    opportunity_score = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Score d’opportunité",
    )

    postponed_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Reportée jusqu'au",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="detected",
        verbose_name="Statut",
    )

    detected_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Détecté le",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Mis à jour le",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )

    image = models.ImageField(
        upload_to="product_opportunities/",
        blank=True,
        null=True,
        verbose_name="Image",
    )

    recommended_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Prix de vente conseillé",
    )

    initial_stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock initial",
    )

    supplier_offer = models.ForeignKey(
        "product_intelligence.SupplierOffer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opportunities",
        verbose_name="Offre fournisseur",
    )

    restock_product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="restock_opportunities",
        verbose_name="Produit à réapprovisionner",
    )

    published_product = models.OneToOneField(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_opportunity",
        verbose_name="Produit publié",
    )

    category = models.ForeignKey(
        "products.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_opportunities",
        verbose_name="Catégorie",
    )

    class Meta:
        ordering = ["-opportunity_score", "-detected_at"]
        verbose_name = "Opportunité produit"
        verbose_name_plural = "Opportunités produits"

    def __str__(self):
        return self.name

    def get_total_cost(self):
        return OpportunityAnalyzer.total_cost(self)

    def get_estimated_margin(self):
        return OpportunityAnalyzer.estimated_margin(self)

    def get_margin_percent(self):
        return OpportunityAnalyzer.margin_percent(self)

    def get_recommended_price(self):
        return OpportunityAnalyzer.recommended_price(self)

    def calculate_opportunity_score(self):
        return OpportunityAnalyzer.opportunity_score(self)

    def save(self, *args, **kwargs):
        self.opportunity_score = self.calculate_opportunity_score()
        super().save(*args, **kwargs)

class ProductIdea(models.Model):

    STATUS_CHOICES = [
        (
            "proposed",
            "Proposée",
        ),
        (
            "selected",
            "Sélectionnée",
        ),
        (
            "rejected",
            "Écartée",
        ),
        (
            "validated",
            "Validée",
        ),
    ]

    name = models.CharField(
        max_length=255,
        verbose_name="Nom de l'idée",
    )

    customer_problem = models.TextField(
        verbose_name="Problème client",
    )

    target_customer = models.TextField(
        verbose_name="Client cible",
    )

    reason_to_study = models.TextField(
        verbose_name=(
            "Raison de l'étude"
        ),
    )

    countries = models.JSONField(
        default=list,
        verbose_name="Pays ciblés",
    )

    search_keywords = models.JSONField(
        default=list,
        verbose_name=(
            "Mots-clés de recherche"
        ),
    )

    source = models.CharField(
        max_length=100,
        default="openai",
        verbose_name="Origine",
    )

    model_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Modèle utilisé",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="proposed",
        verbose_name="Statut",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créée le",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Mise à jour le",
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        verbose_name = "Idée produit"

        verbose_name_plural = (
            "Idées produits"
        )

    def __str__(self):
        return self.name

    @property
    def is_validated(self):
        return self.status == "validated"

class MarketObservation(models.Model):
    source = models.CharField(
        max_length=50,
    )

    external_id = models.CharField(
        max_length=255,
    )

    name = models.CharField(
        max_length=255,
    )

    description = models.TextField(
        blank=True,
    )

    observed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    currency = models.CharField(
        max_length=3,
        default="EUR",
    )

    product_url = models.URLField(
        blank=True,
    )

    image_url = models.URLField(
        blank=True,
    )

    observed_at = models.DateTimeField(
        auto_now_add=True,
    )

    raw_data = models.JSONField(
        default=dict,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "source",
                    "external_id",
                ],
                name="unique_market_observation",
            )
        ]

    def __str__(self):
        return f"{self.source} - {self.name}"


class MarketObservationSnapshot(models.Model):
    observation = models.ForeignKey(
        MarketObservation,
        related_name="snapshots",
        on_delete=models.CASCADE,
    )

    observed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    currency = models.CharField(
        max_length=3,
        default="EUR",
    )

    observed_at = models.DateTimeField(
        auto_now_add=True,
    )

    raw_data = models.JSONField(
        default=dict,
        blank=True,
    )

    class Meta:
        ordering = [
            "-observed_at",
        ]

    def __str__(self):
        return (
            f"{self.observation.source} - "
            f"{self.observation.name} - "
            f"{self.observed_price}"
        )


class Supplier(models.Model):
    name = models.CharField(
        max_length=255,
    )

    country = models.CharField(
        max_length=2,
    )

    website = models.URLField(
        blank=True,
    )

    supplier_type = models.CharField(
        max_length=50,
    )

    def __str__(self):
        return self.name


class SupplierOffer(models.Model):
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="offers",
    )

    market_observation = models.ForeignKey(
        MarketObservation,
        on_delete=models.CASCADE,
        related_name="supplier_offers",
        null=True,
        blank=True,
    )

    product_name = models.CharField(
        max_length=255,
    )

    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
    )

    shipping_days = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    shipping_country = models.CharField(
        max_length=2,
        blank=True,
        default="",
    )

    currency = models.CharField(
        max_length=3,
        default="EUR",
    )

    stock = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    is_available = models.BooleanField(
        null=True,
        blank=True,
    )

    product_url = models.URLField(
        blank=True,
    )

    observed_at = models.DateTimeField(
        default=timezone.now,
    )

    supplier_product_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
    )

    image_url = models.URLField(
        blank=True,
        default="",
    )

    variant_features = models.JSONField(
        default=dict,
        blank=True,
    )

    def __str__(self):
        return f"{self.supplier} - {self.product_name}"

class MarketplaceStudy(models.Model):

    STATUS_CHOICES = [
        (
            "draft",
            "Brouillon",
        ),
        (
            "running",
            "En cours",
        ),
        (
            "completed",
            "Terminée",
        ),
        (
            "failed",
            "Échouée",
        ),
    ]

    product_idea = models.ForeignKey(
        ProductIdea,
        on_delete=models.CASCADE,
        related_name="marketplace_studies",
        verbose_name="Idée produit",
    )

    marketplaces = models.JSONField(
        default=list,
        verbose_name="Marketplaces ciblées",
    )

    queries = models.JSONField(
        default=list,
        verbose_name="Requêtes ciblées",
    )

    observations = models.ManyToManyField(
        "product_intelligence.MarketObservation",
        related_name="marketplace_studies",
        blank=True,
        verbose_name="Observations collectées",
    )

    max_pages_per_marketplace = (
        models.PositiveSmallIntegerField(
            default=2,
            verbose_name=(
                "Pages maximum par marketplace"
            ),
        )
    )

    max_results_per_query = (
        models.PositiveSmallIntegerField(
            default=20,
            verbose_name=(
                "Résultats maximum par requête"
            ),
        )
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        verbose_name="Statut",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créée le",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Mise à jour le",
    )

    class Meta:
        ordering = [
            "-created_at",
        ]
        verbose_name = "Étude marketplace"
        verbose_name_plural = (
            "Études marketplace"
        )

    def __str__(self):
        return (
            f"Étude #{self.pk} — "
            f"{self.product_idea.name}"
        )
