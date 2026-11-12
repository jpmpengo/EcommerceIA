import ssl

import httpx
import truststore
from django.db import transaction
from django.utils import timezone
from openai import OpenAI

from product_intelligence.models import (
    ProductIdea,
    ProductIdeaVisualReference,
)
from product_intelligence.services.openai_client import (
    OpenAIClient,
)
from product_intelligence.services.product_idea_discovery import (
    ProductIdeaDiscoveryService,
)
from product_intelligence.services.product_idea_diversity import ProductIdeaDiversityService
from product_intelligence.services.product_idea_duplicate_qualification import ProductIdeaDuplicateQualificationService
from product_intelligence.services.product_idea_evidence_verification import ProductIdeaEvidenceVerificationService
from product_intelligence.services.product_idea_score_service import (
    ProductIdeaScoreService,
)


class ProductIdeaGenerationService:

    DEFAULT_MODEL = "gpt-5.6-luna"

    @classmethod
    def generate(
        cls,
        model=None,
    ):
        if ProductIdea.objects.filter(
            status="proposed",
        ).exists():
            raise ValueError(
                (
                    "Des idées sont déjà "
                    "en attente d’examen."
                )
            )

        selected_model = (
            model
            or cls.DEFAULT_MODEL
        )

        discovery_service = (
            cls._build_discovery_service(
                model=selected_model,
            )
        )

        previous_ideas = list(ProductIdea.objects.order_by("pk").values("name", "supplier_search_keywords", "category_path", "customer_problem", "reason_to_study"))
        result = discovery_service.discover(previous_ideas=previous_ideas)
        ideas = result["ideas"]

        if len(ideas) > 5:
            raise ValueError(
                (
                    "OpenAI doit proposer "
                    "au maximum cinq idées."
                )
            )

        diversity = ProductIdeaDiversityService.check(ideas)
        if not diversity["valid"]:
            result = discovery_service.discover(previous_ideas=previous_ideas)
            ideas = result["ideas"]
            if len(ideas) > 5:
                raise ValueError("OpenAI doit proposer au maximum cinq idées.")
            diversity = ProductIdeaDiversityService.check(ideas)
            if not diversity["valid"]:
                raise ValueError(f"Diversification des idees insuffisante apres deux tentatives : {diversity}")

        historical_check = ProductIdeaDiversityService.check_historical_duplicates(ideas, previous_ideas)
        if not historical_check["valid"]:
            duplicate_names = set(historical_check["duplicates"])
            ideas = [idea for idea in ideas if idea["name"] not in duplicate_names]
        if not ideas:
            return 0
        qualifications = cls._qualify_historical_similarities(ideas, previous_ideas, discovery_service.client)
        ideas = cls._filter_qualified_ideas(ideas, qualifications)
        if not ideas:
            return 0

        cls._save_ideas(
            ideas=ideas,
            model=selected_model,
        )

        return len(ideas)

    @classmethod
    def _qualify_historical_similarities(cls, ideas, previous_ideas, client):
        qualifier = ProductIdeaDuplicateQualificationService(client)
        matches = ProductIdeaDiversityService.find_similar_historical_ideas(ideas, previous_ideas)
        matches.sort(key=lambda row: row["similarity"], reverse=True)
        results = []
        verifier = None
        stopped = set()
        for match in matches:
            name = match["idea"]
            if name in stopped:
                continue
            idea = next(row for row in ideas if row.get("name") == name)
            previous = next(row for row in previous_ideas if row.get("name") == match["previous_idea"])
            qualification = qualifier.qualify(idea, previous)
            evidence_verified = False
            if qualification["decision"] == "innovation":
                if verifier is None:
                    verifier = ProductIdeaEvidenceVerificationService()
                technical_verified = verifier.verify_innovation(qualification.get("evidence_url", ""), qualification.get("functional_difference", "")).is_verified
                if technical_verified:
                    source_content = verifier.fetch_innovation_content(qualification.get("evidence_url", ""))
                    if source_content:
                        functional_check = qualifier.verify_innovation_evidence(idea, previous, qualification.get("functional_difference", ""), source_content)
                        evidence_verified = functional_check["is_supported"] is True
            results.append({**match, **qualification, "evidence_verified": evidence_verified, "unreviewed_matches": 0})
            if qualification["decision"] == "duplicate":
                stopped.add(name)
        return results

    @staticmethod
    def _filter_qualified_ideas(ideas, qualifications):
        rejected = {row["idea"] for row in qualifications if row["decision"] == "duplicate" or (row["decision"] == "innovation" and not row.get("evidence_verified", False)) or row.get("unreviewed_matches", 0) > 0}
        return [idea for idea in ideas if idea.get("name") not in rejected]

    @staticmethod
    def _build_discovery_service(
        model,
    ):
        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        http_client = httpx.Client(
            verify=ssl_context,
            timeout=180.0,
        )

        sdk_client = OpenAI(
            http_client=http_client
        )

        client = OpenAIClient(
            client=sdk_client,
            model=model,
        )

        discovery_service = ProductIdeaDiscoveryService(
            client=client
        )
        return discovery_service

    @staticmethod
    def _normalize_demand_signal_assessments(assessments):
        normalized = []
        for assessment in assessments:
            item = dict(assessment)
            observed_at = item.get("observed_at")
            if hasattr(observed_at, "isoformat"):
                item["observed_at"] = observed_at.isoformat()
            normalized.append(item)
        return normalized

    @staticmethod
    def _verify_growth_signals(signals, verifier=None):
        verifier = verifier or ProductIdeaEvidenceVerificationService()
        result = []
        for signal in signals:
            item = dict(signal)
            value = str(item.get("value", "")).lower()
            if (item.get("metric") == "search_trend" and "% growth" in value) or (item.get("metric") == "sales_growth"):
                item["is_verified"] = verifier.verify(item.get("source_url", ""), item["metric"], item["value"]).is_verified
            if item.get("metric") == "search_trend" and "is_verified" not in item:
                item["is_verified"] = False
            result.append(item)
        return result

    @staticmethod
    def _verify_delivery_evidence(items, verifier=None):
        verifier = verifier or ProductIdeaEvidenceVerificationService()
        results = []
        for item in items or []:
            row = dict(item)
            row["is_verified"] = False
            if row.get("status") != "unknown" and row.get("source_url") and row.get("delivery_days_min") is not None and row.get("delivery_days_max") is not None:
                row["is_verified"] = verifier.verify_delivery(row["source_url"], row["delivery_days_min"], row["delivery_days_max"], row.get("competitor_product_name", ""), row.get("country", "")).is_verified
            results.append(row)
        return results

    @staticmethod
    @transaction.atomic
    def _save_ideas(
        ideas,
        model,
    ):
        def localized_keywords_to_dict(items):
            result = {"FR": {}, "BE": {}, "ES": {}}
            for item in items or []:
                keyword = item.get("supplier_search_keyword")
                if not keyword:
                    continue
                for country_code in ("FR", "BE", "ES"):
                    value = item.get(country_code)
                    if value:
                        result[country_code][keyword] = value
            return result

        verified_ideas = [(idea, ProductIdeaGenerationService._normalize_demand_signal_assessments(ProductIdeaGenerationService._verify_growth_signals(idea["demand_signal_assessments"]))) for idea in ideas]

        created_ideas = ProductIdea.objects.bulk_create(
            [
                ProductIdea(
                    name=idea["name"],
                    customer_problem=idea["customer_problem"],
                    target_customer=idea["target_customer"],
                    reason_to_study=idea["reason_to_study"],
                    countries=idea["countries"],
                    category_path=idea["category_path"],
                    search_keywords=idea["search_keywords"],
                    supplier_search_keywords=idea["supplier_search_keywords"],
                    supplier_search_keywords_localized=localized_keywords_to_dict(
                        idea.get("supplier_search_keywords_localized", [])
                    ),
                    demand_signals=idea["demand_signals"],
                    demand_signal_assessments=verified_signals,
                    idea_score=ProductIdeaScoreService.calculate(verified_signals, reference_date=timezone.localdate()),
                    evidence_sources=idea["evidence_sources"],
                    competitor_delivery_evidence=ProductIdeaGenerationService._verify_delivery_evidence(idea.get("competitor_delivery_evidence", [])),
                    source="openai",
                    model_name=model,
                    status="proposed",
                )
                for idea, verified_signals in verified_ideas
            ]
        )

        visual_references = []
        for created_idea, idea in zip(created_ideas, ideas):
            for reference in idea.get("visual_references", []):
                visual_references.append(
                    ProductIdeaVisualReference(
                        product_idea=created_idea,
                        supplier_search_keyword=reference["supplier_search_keyword"],
                        product_name=reference.get("product_name", ""),
                        source_title=reference.get("source_title", ""),
                        source_url=reference.get("source_url", ""),
                        image_url=reference["image_url"],
                        model_name=model,
                    )
                )

        ProductIdeaVisualReference.objects.bulk_create(
            visual_references
        )
