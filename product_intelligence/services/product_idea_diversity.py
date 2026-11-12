from collections import Counter

from products.services.category_normalization import CategoryNormalizationService


class ProductIdeaDiversityService:
    MIN_FAMILIES = 3
    MAX_PER_FAMILY = 2

    @classmethod
    def name_similarity(cls, idea, previous_idea):
        normalize = CategoryNormalizationService.normalize
        stopwords = {"a", "au", "aux", "avec", "de", "des", "du", "en", "et", "la", "le", "les", "pour", "sans", "un", "une", "d", "l"}
        def tokens(row):
            return set(normalize(row.get("name", "")).split()) - stopwords
        current = tokens(idea)
        previous = tokens(previous_idea)
        union = current | previous
        return round(len(current & previous) / len(union), 3) if union else 0.0

    @classmethod
    def keyword_similarity(cls, idea, previous_idea):
        normalize = CategoryNormalizationService.normalize
        def tokens(row):
            return set(normalize(" ".join(row.get("supplier_search_keywords") or [])).split())
        current = tokens(idea)
        previous = tokens(previous_idea)
        union = current | previous
        return round(len(current & previous) / len(union), 3) if union else 0.0

    @classmethod
    def find_similar_historical_ideas(cls, ideas, previous_ideas, threshold=0.4):
        matches = []
        for idea in ideas:
            for previous in previous_ideas:
                old = previous if isinstance(previous, dict) else {"name": str(previous)}
                name_score = cls.name_similarity(idea, old)
                keyword_score = cls.keyword_similarity(idea, old)
                score = max(name_score, keyword_score)
                if score >= threshold:
                    matches.append({"idea": idea.get("name", ""), "previous_idea": old.get("name", ""), "similarity": score, "name_similarity": name_score, "keyword_similarity": keyword_score})
        return matches

    @classmethod
    def check_historical_duplicates(cls, ideas, previous_ideas):
        normalize = CategoryNormalizationService.normalize
        historical = []
        for item in previous_ideas:
            row = item if isinstance(item, dict) else {"name": str(item)}
            historical.append({"name": normalize(row.get("name", "")), "keywords": {normalize(k) for k in (row.get("supplier_search_keywords") or [])}, "family": normalize((row.get("category_path") or [""])[0])})
        duplicates = []
        for idea in ideas:
            name = normalize(idea.get("name", ""))
            keywords = {normalize(k) for k in (idea.get("supplier_search_keywords") or [])}
            family = normalize((idea.get("category_path") or [""])[0])
            if name and any(name == old["name"] for old in historical):
                duplicates.append(idea.get("name", ""))
        return {"valid": not duplicates, "duplicates": duplicates}

    @classmethod
    def check(cls, ideas):
        families = []
        for idea in ideas:
            path = idea.get("category_path") or []
            name = str(path[0]).strip() if path else ""
            key = CategoryNormalizationService.normalize(name)
            aliases = CategoryNormalizationService.ALIASES
            canonical = next((target for alias, target in aliases.items() if CategoryNormalizationService.normalize(alias) == key), name)
            families.append(CategoryNormalizationService.normalize(canonical) or "unknown")
        counts = Counter(families)
        valid = len(counts) >= min(cls.MIN_FAMILIES, len(ideas)) and all(count <= cls.MAX_PER_FAMILY for count in counts.values()) and "unknown" not in counts
        return {"valid": valid, "families": dict(counts), "distinct_families": len(counts), "issues": (["Diversification insuffisante"] if not valid else [])}
