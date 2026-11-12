import contextlib
import io
import json
import traceback
from datetime import datetime
from pathlib import Path
from django.core.management import call_command
from django.core.management.base import BaseCommand
from orders.services.backoffice_cycle_report import BackofficeCycleReport


class Command(BaseCommand):
    help = "Execute manuellement six cycles du pipeline back-office."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        if not 1 <= options["limit"] <= 100:
            raise ValueError("Limite invalide (1 a 100).")
        folder = Path("logs/backoffice")
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / ("backoffice_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".log")
        successes = 0
        failures = 0
        total_operations = 0
        total_incidents = 0
        incident_cycles = 0
        with path.open("w", encoding="utf-8") as journal:
            for cycle in range(1, 7):
                capture = io.StringIO()
                error = None
                try:
                    with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
                        call_command("run_nightly_order_pipeline", limit=options["limit"], dry_run=options["dry_run"], stdout=capture, stderr=capture)
                except Exception as exc:
                    error = str(exc)
                    capture.write(traceback.format_exc())
                    failures += 1
                else:
                    successes += 1
                bilan = BackofficeCycleReport.summarize(capture.getvalue()) if not error and not options["dry_run"] else None
                if bilan:
                    total_operations += bilan["operations"]
                    total_incidents += bilan["incidents"]
                    if bilan["incidents"]:
                        incident_cycles += 1
                title = "CYCLE {} - {}".format(cycle, "ERREUR" if error else "TERMINE")
                journal.write("\n" + title + "\n" + capture.getvalue() + "\n")
                if bilan:
                    journal.write("BILAN METIER : {} - operations={} - incidents={}\n".format(bilan["status"], bilan["operations"], bilan["incidents"]))
                    for detail in bilan["details"]:
                        journal.write(detail + "\n")
                journal.flush()
                self.stdout.write(title)
                if bilan:
                    self.stdout.write("BILAN METIER : {} - operations={} - incidents={}".format(bilan["status"], bilan["operations"], bilan["incidents"]))
                    for detail in bilan["details"]:
                        self.stdout.write("  " + detail)
                if error:
                    self.stdout.write("Erreur : " + error)
                else:
                    self.stdout.write(capture.getvalue().strip() or "Aucun message retourne")
            self.stdout.write("BILAN METIER CUMULE : {} operations, {} signalements incidents sur {} cycles.".format(total_operations, total_incidents, incident_cycles))
            summary = "BILAN FINAL : {} cycle(s) termine(s), {} cycle(s) en erreur. Journal : {}".format(successes, failures, path)
            journal.write("\n" + summary + "\n")
            self.stdout.write(summary)
