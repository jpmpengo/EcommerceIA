from django.core.management.base import BaseCommand
from orders.services.supplier_pipeline_preparation_step import SupplierPipelinePreparationStep
from orders.services.supplier_pipeline_submission_step import SupplierPipelineSubmissionStep
from orders.services.supplier_pipeline_confirmation_step import SupplierPipelineConfirmationStep
from orders.services.supplier_pipeline_payment_step import SupplierPipelinePaymentStep
from orders.services.supplier_pipeline_logistics_step import SupplierPipelineLogisticsStep
from orders.services.supplier_pipeline_delivery_step import SupplierPipelineDeliveryStep
from orders.services.supplier_pipeline_reception_notification_step import SupplierPipelineReceptionNotificationStep
from orders.services.supplier_pipeline_reception_assumption_step import SupplierPipelineReceptionAssumptionStep
from orders.services.supplier_pipeline_satisfaction_step import SupplierPipelineSatisfactionStep
from orders.services.supplier_pipeline_incident_registry import SupplierPipelineIncidentRegistry


class Command(BaseCommand):
    help = "Pipeline fournisseur V2 - orchestrateur maitre"

    def handle(self, *args, **options):
        operations = 0
        relance = False
        motifs = []
        incidents = []
        etapes = [
            ("Preparation", SupplierPipelinePreparationStep),
            ("Soumission CJ", SupplierPipelineSubmissionStep),
            ("Confirmation CJ", SupplierPipelineConfirmationStep),
            ("Paiement simule CJ", SupplierPipelinePaymentStep),
            ("Suivi logistique CJ", SupplierPipelineLogisticsStep),
            ("Livraison simulee CJ", SupplierPipelineDeliveryStep),
            ("Notification reception Elese", SupplierPipelineReceptionNotificationStep),
            ("Reception presumee", SupplierPipelineReceptionAssumptionStep),
            ('Enquete satisfaction', SupplierPipelineSatisfactionStep),
        ]
        for nom, etape in etapes:
            resultat = etape.run()
            operations += resultat.operations_effectuees
            relance = relance or resultat.relance_demandee
            motifs.extend(resultat.motifs_relance)
            incidents.extend(resultat.incidents)
            if resultat.operations_effectuees:
                self.stdout.write("{} : {} nouvelle(s) operation(s)".format(nom, resultat.operations_effectuees))
        self.stdout.write("Pipeline V2 : {} nouvelle(s) operation(s)".format(operations))
        nouveaux, resolus = SupplierPipelineIncidentRegistry.filter_new(incidents)
        for incident in nouveaux:
            self.stdout.write("NOUVEL INCIDENT : {}".format(incident))
        for incident in resolus:
            self.stdout.write("INCIDENT RESOLU : {}".format(incident))
        if relance and operations:
            self.stdout.write("RELANCE NECESSAIRE : python manage.py run_supplier_pipeline_v2")
        elif relance:
            self.stdout.write("Relance differee : aucune progression durant ce cycle")
        else:
            self.stdout.write("Cycle termine : aucune relance immediate necessaire")
