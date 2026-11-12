import ast


class BackofficeCycleReport:
    @staticmethod
    def parse(output):
        reports = {}
        for line in output.splitlines():
            section, separator, value = line.partition(" : ")
            if separator and section in ("supplier", "notifications", "receptions", "satisfaction"):
                try:
                    parsed = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    continue
                if isinstance(parsed, dict):
                    reports[section] = parsed
        return reports

    @classmethod
    def summarize(cls, output):
        reports = cls.parse(output)
        if not reports:
            return {"status": "AUCUN RESULTAT METIER", "operations": 0, "incidents": 0, "details": []}
        operations = 0
        incidents = 0
        details = []
        success_fields = {"supplier": ("prepared", "submitted", "lifecycle_processed", "monitor_synced"), "notifications": ("sent",), "receptions": ("assumed",), "satisfaction": ("sent",)}
        incident_fields = {"supplier": ("blocked", "failed", "supplier_failed_existing", "lifecycle_failed", "monitor_failed"), "notifications": ("failed",), "receptions": ("failed",), "satisfaction": ()}
        for section, report in reports.items():
            for field in success_fields.get(section, ()):
                count = report.get(field, 0)
                if isinstance(count, int) and count > 0:
                    operations += count
                    details.append("{} : {} = {}".format(section, field, count))
            for field in incident_fields.get(section, ()):
                count = report.get(field, 0)
                if isinstance(count, int) and count > 0:
                    incidents += count
                    details.append("INCIDENT {} : {} = {}".format(section, field, count))
            if section == "satisfaction":
                value = report.get("incidents", [])
                if isinstance(value, list):
                    incidents += len(value)
                    details.extend("INCIDENT satisfaction : {}".format(item) for item in value)
                elif isinstance(value, int) and value > 0:
                    incidents += value
                    details.append("INCIDENT satisfaction : {}".format(value))
        status = "SUCCES AVEC INCIDENTS" if incidents else "TRAVAIL EFFECTUE" if operations else "AUCUNE ACTION NECESSAIRE"
        return {"status": status, "operations": operations, "incidents": incidents, "details": details}
