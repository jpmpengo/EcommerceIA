import traceback
from datetime import datetime
from pathlib import Path
from pprint import pformat

from django.core.management.base import BaseCommand

from product_intelligence.services.product_idea_nightly_orchestrator import (
    ProductIdeaNightlyOrchestratorService,
)


class Command(BaseCommand):
    help = "Execute le traitement nocturne des idees produit proposees."

    def add_arguments(self, parser):
        parser.add_argument("--idea-id", type=int, default=None)

    def handle(self, *args, **options):
        idea_id = options["idea_id"]
        try:
            if idea_id is None:
                result = ProductIdeaNightlyOrchestratorService.run()
            else:
                result = ProductIdeaNightlyOrchestratorService.run(idea_id=idea_id)
        except Exception as exc:
            folder = Path("logs/ideas")
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / ("ideas_error_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".log")
            path.write_text("ECHEC PIPELINE IDEES\n" + traceback.format_exc(), encoding="utf-8")
            self.stderr.write("ECHEC PIPELINE IDEES : {}".format(exc))
            self.stderr.write("Journal : {}".format(path))
            raise
        reports = result.get("analysis_reports", [])
        recommendations = result.get("recommendation_reports", [])
        retry = result.get("retry_results", {})
        failures = result.get("failures", []) + retry.get("failures", [])
        keys = ("offers_analyzed", "offers_retained", "offers_unprofitable", "offers_customs_excluded", "offers_incomplete", "opportunities_created", "opportunities_existing")
        totals = {key: sum(report.get(key, 0) for report in reports) for key in keys}
        output = ["BILAN PIPELINE IDEES"]
        generated_ids = result.get("generated_idea_ids", [])
        output.append("Nouvelles idees generees : {}".format(len(generated_ids)))
        output.append("Identifiants des nouvelles idees : {}".format(generated_ids))
        output.append("Idees analysees : {}".format(len(result.get("succeeded_ids", []))))
        output.append("Idees en echec : {}".format(len(result.get("failed_ids", []))))
        labels = {"offers_analyzed": "Offres analysees", "offers_retained": "Offres retenues", "offers_unprofitable": "Offres non rentables", "offers_customs_excluded": "Offres exclues douane", "offers_incomplete": "Offres incompletes", "opportunities_created": "Opportunites creees", "opportunities_existing": "Opportunites existantes"}
        for key in keys:
            output.append("{} : {}".format(labels[key], totals[key]))
        output.append("Recommandations IA terminees : {}".format(len(recommendations)))
        output.append("Opportunites reprises : {}".format(len(retry.get("processed", []))))
        output.append("Incidents : {}".format(len(failures)))
        activity = bool(generated_ids or result.get("succeeded_ids") or recommendations or retry.get("processed"))
        output.append("STATUT : {}".format("AVEC INCIDENTS" if failures else "TRAVAIL EFFECTUE" if activity else "AUCUNE ACTION NECESSAIRE"))
        for failure in failures:
            output.append("INCIDENT : {}".format(failure))
        folder = Path("logs/ideas")
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / ("ideas_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".log")
        path.write_text("\n".join(output) + "\n\nDETAILS ORCHESTRATEUR\n" + pformat(result) + "\n", encoding="utf-8")
        for line in output:
            self.stdout.write(line)
        self.stdout.write("Journal : {}".format(path))
