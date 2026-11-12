import re
import unicodedata
from products.models import Category

class CategoryNormalizationService:
    ALIASES = {
        'conservation des aliments': 'Conservation alimentaire',
        'cafe': 'Café et boissons',
        'chien': 'Accessoires pour chiens',
        'climatisation personnelle': 'Rafraîchissement personnel',
        'soin du visage': 'Soins du visage',

        'gamelles anti-glouton pour chiens': 'gamelles anti-glouton',
        'alimentation pour chiens': 'Alimentation canine',
        'animaux': 'Animaux de compagnie',
        'cuisine': 'Maison & Cuisine',
        'maison': 'Maison & Cuisine',
        'maison et jardin': 'Maison & Cuisine',
        'maison et confort': 'Maison & Cuisine',
        'beaute': 'Hygiène & Bien-être',
        'beaute et soins personnels': 'Hygiène & Bien-être',
        'hygiene intime': 'Hygiène & Bien-être',
        'electronique grand public': 'Électronique',
        'sport et fitness': 'Sport & Fitness',
    }

    @staticmethod
    def normalize(value):
        value = unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode('ascii').lower()
        return ' '.join(re.sub('[^a-z0-9]+', ' ', value).split())

    @classmethod
    def canonical_name(cls, name):
        key = cls.normalize(name)
        return next((target for alias, target in cls.ALIASES.items() if cls.normalize(alias) == key), str(name).strip())

    @classmethod
    def propose(cls, category_path):
        path = [str(item).strip() for item in (category_path or []) if str(item).strip()]
        categories = list(Category.objects.all())
        matches = []
        parent = None
        missing = False
        for index, name in enumerate(path):
            key = cls.normalize(name)
            key = cls.normalize(cls.canonical_name(name))
            match = next((c for c in categories if cls.normalize(c.name) == key and c.parent_id == (parent.id if parent else None)), None) if not missing else None
            matches.append(dict(proposed=name, category_id=match.id if match else None, matched_name=match.name if match else None, needs_approval=match is None))
            if match is None:
                missing = True
            parent = match
        return matches
