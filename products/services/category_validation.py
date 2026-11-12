from products.services.category_normalization import CategoryNormalizationService


class CategoryValidationService:
    @classmethod
    def validate(cls, category_path):
        if not isinstance(category_path, list) or len(category_path) != 3:
            return False
        if any(not isinstance(name, str) or not name.strip() or len(name.strip()) < 3 or len(name.strip()) > 100 for name in category_path):
            return False
        normalized = [CategoryNormalizationService.normalize(name) for name in category_path]
        if any(not name for name in normalized) or len(set(normalized)) != 3:
            return False
        return True
