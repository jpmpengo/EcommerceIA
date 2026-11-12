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

    saturation_level = models.CharField(max_length=20, default="indeterminate")
    saturation_evidence = models.JSONField(default=dict, blank=True)
    opportunity_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        default=None,
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

    projected_profit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Benefice net previsionnel",
    )

    projected_margin_rate = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Marge nette previsionnelle (%)",
    )

    initial_stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock initial",
    )

    market_collection_batch_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Lot de prix comparables utilisé",
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

    category_path = models.JSONField(
        default=list,
        verbose_name="Chemin de catégorie",
    )

    demand_signals = models.JSONField(
        default=list,
        verbose_name=(
            "Signaux de demande"
        ),
    )

    demand_signal_assessments = models.JSONField(
        default=list,
        verbose_name=(
            "Qualifications des signaux de demande"
        ),
    )

    competitor_delivery_evidence = models.JSONField(
        default=list,
        verbose_name="Preuves des delais concurrents",
    )

    evidence_sources = models.JSONField(
        default=list,
        verbose_name=(
            "Sources justificatives"
        ),
    )

    search_keywords = models.JSONField(
        default=list,
        verbose_name=(
            "Mots-clés de recherche"
        ),
    )

    supplier_search_keywords = models.JSONField(
        default=list,
        verbose_name=(
            "Mots-clés de recherche fournisseur"
        ),
    )

    supplier_search_keywords_localized = models.JSONField(
        default=dict,
        verbose_name=(
            "Mots-clés fournisseur localisés pour CJ Europe"
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

    idea_score = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Score de l idee",
    )

    selection_source = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Origine de la selection",
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

class ProductIdeaVisualReference(models.Model):

    product_idea = models.ForeignKey(
        ProductIdea,
        on_delete=models.CASCADE,
        related_name="visual_references",
    )

    supplier_search_keyword = models.CharField(
        max_length=255,
    )

    product_name = models.CharField(
        max_length=500,
        blank=True,
        default="",
    )

    source_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    source_url = models.URLField(
        max_length=1000,
        blank=True,
        default="",
    )

    image_url = models.URLField(
        max_length=1000,
    )

    model_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

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

    product_idea = models.ForeignKey(
        ProductIdea,
        on_delete=models.CASCADE,
        related_name="supplier_offers",
        null=True,
        blank=True,
    )

    product_name = models.CharField(
        max_length=255,
    )

    product_description = models.TextField(
        blank=True,
        default=str(),
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

    free_shipping = models.BooleanField(
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

    shipping_method = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    customs_included = models.BooleanField(
        null=True,
        blank=True,
    )

    currency = models.CharField(
        max_length=3,
        default="EUR",
    )

    stock = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    shipping_weight_grams = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    stock_country = models.CharField(
        max_length=2,
        blank=True,
        default="",
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

    supplier_parent_product_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
    )

    supplier_search_keyword = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    supplier_sku = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
    )

    supplier_verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    image_url = models.URLField(
        blank=True,
        default="",
    )

    variant_features = models.JSONField(
        default=dict,
        blank=True,
    )

    visual_match_classification = models.CharField(
        max_length=20,
        blank=True,
        default="",
    )

    visual_score = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    same_product_probability = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    visual_match_evidence = models.TextField(
        blank=True,
        default="",
    )

    visual_match_differences = models.JSONField(
        default=list,
        blank=True,
    )

    def __str__(self):
        return f"{self.supplier} - {self.product_name}"

class ComparablePrice(models.Model):

    QUALIFICATION_STATUS_CHOICES = [
        (
            "collected",
            "Collecté",
        ),
        (
            "retained",
            "Retenu",
        ),
        (
            "rejected",
            "Rejeté",
        ),
    ]

    supplier_offer = models.ForeignKey(
        SupplierOffer,
        on_delete=models.CASCADE,
        related_name="comparable_prices",
    )

    product_name = models.CharField(
        max_length=255,
    )

    commercial_segment = models.CharField(max_length=20, default="unclassified", choices=[("unclassified", "Non classe"), ("direct", "Comparable direct"), ("different_segment", "Gamme differente")])
    commercial_segment_reason = models.TextField(null=True, blank=True)
    observed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    currency = models.CharField(
        max_length=3,
        default="EUR",
    )

    source_title = models.CharField(
        max_length=255,
    )

    source_url = models.URLField(
        max_length=1000,
    )

    image_url = models.URLField(
        max_length=1000,
        blank=True,
        default="",
    )

    shipping_days_min = models.PositiveIntegerField(null=True, blank=True)
    shipping_days_max = models.PositiveIntegerField(null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shipping_currency = models.CharField(max_length=3, null=True, blank=True)
    free_shipping = models.BooleanField(null=True, blank=True)
    shipping_destination_country = models.CharField(max_length=2, null=True, blank=True)
    shipping_evidence = models.TextField(null=True, blank=True)

    search_query = models.CharField(
        max_length=500,
    )

    qualification_status = models.CharField(
        max_length=20,
        choices=(
            QUALIFICATION_STATUS_CHOICES
        ),
        default="collected",
    )

    qualification_reason = models.TextField(
        blank=True,
        default="",
    )

    evidence = models.TextField(
        blank=True,
        default="",
    )

    model_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    collection_batch_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
    )

    is_current = models.BooleanField(
        default=True,
        db_index=True,
    )

    observed_at = models.DateTimeField(
        default=timezone.now,
    )

    class Meta:
        ordering = [
            "-observed_at",
        ]

    def __str__(
        self,
    ):
        return (
            f"{self.product_name} - "
            f"{self.observed_price} "
            f"{self.currency}"
        )


class OpportunityAIRecommendation(models.Model):
    opportunity = models.OneToOneField("product_intelligence.ProductOpportunity", on_delete=models.CASCADE, related_name="ai_recommendation")
    decision = models.CharField(max_length=20, choices=[("recommend", "Recommander"), ("study", "Etudier"), ("reject", "Deconseiller")])
    summary = models.TextField()
    merchant_summary = models.TextField(blank=True, default="", verbose_name="Synthese commerciale pour le commercant")
    commercial_name = models.CharField(max_length=255, blank=True, default="")
    commercial_description = models.TextField(blank=True, default="")
    category_path = models.JSONField(default=list, blank=True)
    category_reason = models.TextField(blank=True, default="")
    model_name = models.CharField(max_length=100, blank=True, default="")
    study_blockers = models.JSONField(default=list, blank=True)
    completion_history = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
