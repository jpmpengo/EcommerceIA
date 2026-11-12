from dataclasses import dataclass, field


@dataclass
class SupplierPipelineResult:
    operations_effectuees: int = 0
    relance_demandee: bool = False
    motifs_relance: list = field(default_factory=list)
    incidents: list = field(default_factory=list)
