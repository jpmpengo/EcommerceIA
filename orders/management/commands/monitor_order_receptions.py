from django.core.management.base import BaseCommand, CommandError

from orders.services.reception_monitoring_runner import ReceptionMonitoringRunner


class Command(BaseCommand):
    help = "Traite les receptions presumees des commandes clients."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--send-requests", action="store_true")

    def handle(self, *args, **options):
        limit = options["limit"]
        if not 1 <= limit <= 100:
            raise CommandError("Limite invalide (1 a 100).")
        if options["send_requests"]:
            from django.conf import settings
            from urllib.parse import urlparse
            if options["dry_run"]:
                dossiers = list(ReceptionMonitoringRunner.get_orders_to_notify()[:limit])
                self.stdout.write("SIMULATION - aucun email envoye")
                self.stdout.write("Dossiers selectionnes : {}".format(len(dossiers)))
                self.stdout.write("IDs : {}".format([o.id for o in dossiers]))
                return
            if not settings.ORDER_RECEPTION_AUTO_EMAIL_ENABLED:
                raise CommandError("Notifications automatiques desactivees.")
            test_mode = getattr(settings, "ORDER_RECEPTION_TEST_MODE", False)
            site_url = "http://127.0.0.1:8000" if test_mode else getattr(settings, "ORDER_RECEPTION_SITE_URL", "")
            parsed = urlparse(site_url)
            if not test_mode and (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
                raise CommandError("URL publique HTTPS requise pour les notifications.")
            if test_mode and settings.ORDER_RECEPTION_TEST_EMAIL != "jpmpengo@yahoo.fr":
                raise CommandError("Adresse de test non autorisee.")
            result = ReceptionMonitoringRunner.run_notifications(site_url, limit=limit)
            self.stdout.write("Dossiers selectionnes : {}".format(result["selected"]))
            self.stdout.write("Emails envoyes : {}".format(result["sent"]))
            self.stdout.write("Dossiers ignores : {}".format(result["skipped"]))
            self.stdout.write("Erreurs : {}".format(result["failed"]))
            return
        if options["dry_run"]:
            dossiers = list(ReceptionMonitoringRunner.get_due_orders()[:limit])
            self.stdout.write("SIMULATION - aucune reception modifiee")
            self.stdout.write("Dossiers selectionnes : {}".format(len(dossiers)))
            self.stdout.write("IDs : {}".format([o.id for o in dossiers]))
            return
        result = ReceptionMonitoringRunner.run(limit=limit)
        self.stdout.write("Dossiers selectionnes : {}".format(result["selected"]))
        self.stdout.write("Receptions presumees : {}".format(result["assumed"]))
        self.stdout.write("Dossiers ignores : {}".format(result["skipped"]))
        self.stdout.write("Erreurs : {}".format(result["failed"]))
