from decimal import Decimal
from django.test import TestCase
from product_intelligence.models import Supplier, SupplierOffer, ComparablePrice
from product_intelligence.services.comparable_price_commercial_classification import ComparablePriceCommercialClassificationService

class CommercialClassificationTests(TestCase):
    def test_saves_only_commercial_classification(self):
        supplier = Supplier.objects.create(name='Fournisseur test', country='CN', website='https://example.com', supplier_type='dropshipper')
        offer = SupplierOffer.objects.create(supplier=supplier, product_name='Bague connectee', purchase_price=Decimal('10.00'), currency='EUR')
        comparable = ComparablePrice.objects.create(supplier_offer=offer, product_name='Bague test', observed_price=Decimal('53.99'), currency='EUR', source_title='Boutique test', source_url='https://example.com/bague', qualification_status='retained', is_current=True)
        result = {'classifications': [{'comparable_id': comparable.id, 'commercial_segment': 'direct', 'commercial_segment_reason': 'Fonctions equivalentes'}]}
        count = ComparablePriceCommercialClassificationService.save_classifications(offer, [comparable], result)
        comparable.refresh_from_db()
        self.assertEqual(count, 1)
        self.assertEqual(comparable.commercial_segment, 'direct')
        self.assertEqual(comparable.commercial_segment_reason, 'Fonctions equivalentes')
        self.assertEqual(comparable.observed_price, Decimal('53.99'))
        self.assertEqual(comparable.qualification_status, 'retained')

    def test_rejects_unknown_comparable_id(self):
        supplier = Supplier.objects.create(name='Fournisseur test', country='CN', website='https://example.com', supplier_type='dropshipper')
        offer = SupplierOffer.objects.create(supplier=supplier, product_name='Bague connectee', purchase_price=Decimal('10.00'), currency='EUR')
        comparable = ComparablePrice.objects.create(supplier_offer=offer, product_name='Bague test', observed_price=Decimal('53.99'), currency='EUR', source_title='Boutique test', source_url='https://example.com/bague', qualification_status='retained', is_current=True)
        result = {'classifications': [{'comparable_id': comparable.id + 999, 'commercial_segment': 'direct', 'commercial_segment_reason': 'Fonctions equivalentes'}]}
        with self.assertRaises(ValueError):
            ComparablePriceCommercialClassificationService.save_classifications(offer, [comparable], result)
        comparable.refresh_from_db()
        self.assertEqual(comparable.commercial_segment, 'unclassified')

    def test_classify_and_save(self):
        supplier = Supplier.objects.create(name='Fournisseur test', country='CN', website='https://example.com', supplier_type='dropshipper')
        offer = SupplierOffer.objects.create(supplier=supplier, product_name='Bague connectee', purchase_price=Decimal('10.00'), currency='EUR')
        comparable = ComparablePrice.objects.create(supplier_offer=offer, product_name='Bague test', observed_price=Decimal('53.99'), currency='EUR', source_title='Boutique test', source_url='https://example.com/bague', qualification_status='retained', is_current=True)
        class FakeClient:
            def generate(self, **kwargs):
                return {'classifications': [{'comparable_id': comparable.id, 'commercial_segment': 'direct', 'commercial_segment_reason': 'Caracteristiques equivalentes'}]}
        result = ComparablePriceCommercialClassificationService(FakeClient()).classify_and_save(offer, [comparable])
        comparable.refresh_from_db()
        self.assertEqual(result['saved_count'], 1)
        self.assertEqual(comparable.commercial_segment, 'direct')
        self.assertEqual(comparable.observed_price, Decimal('53.99'))

    def test_classify_and_save_researches_unclassified(self):
        from unittest.mock import Mock
        supplier = Supplier.objects.create(name='Fournisseur suivi', country='CN', website='https://example.com', supplier_type='dropshipper')
        offer = SupplierOffer.objects.create(supplier=supplier, product_name='Climatiseur de cou', purchase_price=Decimal('10.00'), currency='EUR')
        comparable = ComparablePrice.objects.create(supplier_offer=offer, product_name='Climatiseur comparable', observed_price=Decimal('36.95'), currency='EUR', source_title='Boutique test', source_url='https://example.com/cou', qualification_status='retained', is_current=True)
        comparable.commercial_segment = 'direct'
        comparable.commercial_segment_reason = 'Ancienne classification'
        comparable.save(update_fields=['commercial_segment', 'commercial_segment_reason'])
        client = Mock()
        client.generate.side_effect = [{'classifications': [{'comparable_id': comparable.id, 'commercial_segment': 'unclassified', 'commercial_segment_reason': 'Informations insuffisantes'}]}, {'classifications': [{'comparable_id': comparable.id, 'commercial_segment': 'direct', 'commercial_segment_reason': 'Meme gamme commerciale confirmee par les fiches techniques'}]}]
        result = ComparablePriceCommercialClassificationService(client).classify_and_save(offer, [comparable])
        comparable.refresh_from_db()
        self.assertEqual(client.generate.call_count, 2)
        self.assertEqual(client.generate.call_args_list[1].kwargs['context']['comparables'][0]['previous_classification_reason'], 'Informations insuffisantes')
        self.assertEqual(result['saved_count'], 1)
        self.assertEqual(comparable.commercial_segment, 'direct')
