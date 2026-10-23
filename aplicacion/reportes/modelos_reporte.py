"""Plantillas mensuales, trimestrales y anuales de reportes."""

from copy import deepcopy
from dataclasses import dataclass, field
from decimal import Decimal

from aplicacion.dominio.contratos.contrato_reporte import (
    IReporteFinanciero,
    IReportePrototype,
)
from aplicacion.dominio.validaciones import limpiar_texto, redondear_moneda
from aplicacion.reportes.estructura_reporte import (
    ComponenteReporte,
    SeccionCompuesta,
)


@dataclass
class ReporteBase(IReporteFinanciero, IReportePrototype):
    """Documento financiero que puede clonarse, construirse y decorarse."""

    tipo: str = "General"
    titulo: str = "Reporte financiero"
    periodo: str = "Sin definir"
    cuerpo: ComponenteReporte = field(
        default_factory=lambda: SeccionCompuesta("Consolidado corporativo")
    )
    graficos: list[str] = field(default_factory=list)
    conclusiones: list[str] = field(default_factory=list)
    total_eur: Decimal = Decimal("0.00")

    def clonar(self) -> "ReporteBase":
        # ============================================================
        # PATRON PROTOTYPE: CLONACION DE PLANTILLAS
        # Este bloque crea una copia profunda para que cada reporte se
        # modifique sin alterar la plantilla mensual, trimestral o anual.
        # Cumple: RF-05 y CU-07.
        # ============================================================
        return deepcopy(self)

    def emitir(self) -> str:
        """Genera una representacion legible del reporte construido."""

        lineas = [
            "FINANCORP S.A.",
            self.titulo,
            f"Tipo: {self.tipo}",
            f"Periodo: {self.periodo}",
            "",
            self.cuerpo.renderizar(),
            "",
            f"TOTAL CONSOLIDADO: {redondear_moneda(self.total_eur)} EUR",
        ]

        if self.graficos:
            lineas.extend(["", "GRAFICOS"])
            lineas.extend(f"- {grafico}" for grafico in self.graficos)

        if self.conclusiones:
            lineas.extend(["", "CONCLUSIONES"])
            lineas.extend(f"- {conclusion}" for conclusion in self.conclusiones)

        return "\n".join(lineas)

    def definir_datos_principales(self, titulo: str, periodo: str) -> None:
        """Actualiza los campos que cambian en cada reporte generado."""

        self.titulo = limpiar_texto(titulo, "titulo del reporte")
        self.periodo = limpiar_texto(periodo, "periodo del reporte")


class ReporteMensual(ReporteBase):
    """Plantilla base para un reporte mensual de ingresos."""

    def __init__(self) -> None:
        super().__init__(
            tipo="Mensual",
            titulo="Reporte mensual de ingresos",
        )


class ReporteTrimestral(ReporteBase):
    """Plantilla base para un reporte trimestral financiero."""

    def __init__(self) -> None:
        super().__init__(
            tipo="Trimestral",
            titulo="Reporte trimestral de gastos e ingresos",
        )


class ReporteAnual(ReporteBase):
    """Plantilla base para un reporte anual consolidado."""

    def __init__(self) -> None:
        super().__init__(
            tipo="Anual",
            titulo="Reporte anual consolidado",
        )


def crear_catalogo_plantillas() -> dict[str, ReporteBase]:
    """Crea el catalogo pequeno requerido por el flujo de reportes."""

    return {
        "mensual": ReporteMensual(),
        "trimestral": ReporteTrimestral(),
        "anual": ReporteAnual(),
    }

