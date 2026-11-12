from django.db import transaction
from product_intelligence.models import ComparablePrice
from typing import Literal
from pydantic import BaseModel, Field

class CommercialClassificationResult(BaseModel):
    comparable_id: int
    commercial_segment: Literal['direct', 'different_segment', 'unclassified']
    commercial_segment_reason: str

class CommercialClassificationResponse(BaseModel):
    classifications: list[CommercialClassificationResult] = Field(default_factory=list)

class ComparablePriceCommercialClassificationService:
    INSTRUCTIONS = 'Tu analyses le SEGMENT COMMERCIAL de produits comparables deja collectes, et non leur seule equivalence fonctionnelle. Pour chaque comparable, retourne comparable_id, commercial_segment (direct, different_segment ou unclassified) et commercial_segment_reason avec des preuves factuelles. Un produit peut avoir les memes fonctions principales que le produit fournisseur tout en appartenant a une gamme commerciale differente. Evalue les materiaux, la technologie, les capteurs, les fonctionnalites supplementaires, la finition, la durabilite, la recharge et le positionnement documente. direct signifie une offre commercialement comparable en gamme et en caracteristiques, meme si les prix different. different_segment exige un faisceau de differences substantielles et documentees indiquant une gamme ou un positionnement distinct. Un prix eleve ou une marque premium ne suffisent jamais seuls. Ne ramene pas automatiquement un produit premium dans direct au seul motif que son usage principal est identique. Si les preuves sont insuffisantes pour trancher, retourne unclassified. Utilise les URL publiques pour verifier les differences lorsque possible. Ne recherche pas de nouveaux comparables, ne modifie aucun prix et justifie chaque decision.'

    FOLLOWUP_INSTRUCTIONS = 'Tu approfondis la classification commerciale des comparables restes unclassified. Recherche sur le Web les fiches techniques du meme produit, verifie les variantes, les caracteristiques contradictoires et les differences documentees avec le produit fournisseur. Ne confonds pas des produits visuellement similaires avec un modele identique. Retourne comparable_id, commercial_segment et commercial_segment_reason. Choisis direct ou different_segment uniquement si les preuves sont suffisantes; sinon conserve unclassified en precisant les incertitudes. Ne recherche pas de nouveaux prix comparables et ne modifie aucun prix.'

    def __init__(self, client):
        self.client = client

    def classify(self, supplier_offer, comparables):
        items = list(comparables)
        context = {
            'supplier_product': {
                'name': supplier_offer.product_name,
            'product_description': supplier_offer.product_description,
                'variant_features': supplier_offer.variant_features or {},
                'product_url': supplier_offer.product_url,
            },
            'comparables': [
                {
                    'comparable_id': item.id,
                    'product_name': item.product_name,
                    'source_url': item.source_url,
                    'evidence': item.evidence,
                    'observed_price': str(item.observed_price),
                    'currency': item.currency,
                } for item in items
            ],
        }
        return self.client.generate(
            instructions=self.INSTRUCTIONS,
            context=context,
            response_model=CommercialClassificationResponse,
            use_web_search=True,
        )

    def classify_unclassified(self, supplier_offer, comparables, first_pass_reasons=None):
        items = list(comparables)
        if not items:
            return {'classifications': []}
        context = {'supplier_product': {'name': supplier_offer.product_name, 'product_description': supplier_offer.product_description, 'variant_features': supplier_offer.variant_features or {}, 'product_url': supplier_offer.product_url}, 'comparables': [{'comparable_id': item.id, 'product_name': item.product_name, 'source_url': item.source_url, 'evidence': item.evidence, 'observed_price': str(item.observed_price), 'currency': item.currency, 'previous_classification_reason': (first_pass_reasons or {}).get(item.id, item.commercial_segment_reason)} for item in items]}
        return self.client.generate(instructions=self.FOLLOWUP_INSTRUCTIONS, context=context, response_model=CommercialClassificationResponse, use_web_search=True)

    @staticmethod
    @transaction.atomic
    def save_classifications(supplier_offer, comparables, result, collection_batch_id=None):
        expected_ids = {item.id for item in comparables}
        classifications = result['classifications']
        received_ids = [item['comparable_id'] for item in classifications]
        if len(received_ids) != len(expected_ids) or set(received_ids) != expected_ids:
            raise ValueError('Identifiants de classification incomplets, inconnus ou dupliques')
        allowed = {'direct', 'different_segment', 'unclassified'}
        for item in classifications:
            if item['commercial_segment'] not in allowed or not str(item.get('commercial_segment_reason') or '').strip():
                raise ValueError('Classification ou justification invalide')
        queryset = ComparablePrice.objects.select_for_update().filter(id__in=expected_ids, supplier_offer=supplier_offer, qualification_status="retained")
        if collection_batch_id is None:
            queryset = queryset.filter(is_current=True)
        else:
            queryset = queryset.filter(collection_batch_id=collection_batch_id)
        rows = list(queryset)
        if len(rows) != len(expected_ids):
            raise ValueError('Comparables modifies ou non admissibles')
        by_id = {item['comparable_id']: item for item in classifications}
        for row in rows:
            item = by_id[row.id]
            row.commercial_segment = item['commercial_segment']
            row.commercial_segment_reason = item['commercial_segment_reason']
        ComparablePrice.objects.bulk_update(rows, ['commercial_segment', 'commercial_segment_reason'])
        return len(rows)

    def classify_and_save(self, supplier_offer, comparables, collection_batch_id=None):
        items = list(comparables)
        if not items:
            raise ValueError('Aucun comparable a classifier')
        result = self.classify(supplier_offer, items)
        pending_ids = {r['comparable_id'] for r in result['classifications'] if r['commercial_segment'] == 'unclassified'}
        if pending_ids:
            pending = [item for item in items if item.id in pending_ids]
            followup = self.classify_unclassified(supplier_offer, pending, {r['comparable_id']: r['commercial_segment_reason'] for r in result['classifications'] if r['comparable_id'] in pending_ids})
            replacements = {r['comparable_id']: r for r in followup['classifications'] if r['comparable_id'] in pending_ids}
            result['classifications'] = [replacements.get(r['comparable_id'], r) for r in result['classifications']]
        count = self.save_classifications(supplier_offer, items, result, collection_batch_id=collection_batch_id)
        return {'saved_count': count, 'classifications': result['classifications']}
