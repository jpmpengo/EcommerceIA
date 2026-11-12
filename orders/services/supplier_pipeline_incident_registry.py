from django.core.cache.backends.filebased import FileBasedCache
from django.conf import settings


class SupplierPipelineIncidentRegistry:
    cache = FileBasedCache(str(settings.BASE_DIR / "supplier_pipeline_v2_cache"), {})
    CACHE_KEY = "supplier_pipeline_v2_reported_incidents"

    @classmethod
    def filter_new(cls, incidents):
        previous = set(cls.cache.get(cls.CACHE_KEY, []))
        current = set(incidents)
        new = sorted(current - previous)
        resolved = sorted(previous - current)
        cls.cache.set(cls.CACHE_KEY, sorted(current), timeout=None)
        return new, resolved
