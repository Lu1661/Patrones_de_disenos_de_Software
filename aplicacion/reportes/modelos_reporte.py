# PLANTILLAS MENSUALES, TRIMESTRALES Y ANUALES DE REPORTES.

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
    # DOCUMENTO FINANCIERO QUE PUEDE CLONARSE, CONSTRUIRSE Y DECORARSE.

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
        # GENERA UNA REPRESENTACION LEGIBLE DEL REPORTE CONSTRUIDO.

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
        # ACTUALIZA LOS CAMPOS QUE CAMBIAN EN CADA REPORTE GENERADO.

        self.titulo = limpiar_texto(titulo, "titulo del reporte")
        self.periodo = limpiar_texto(periodo, "periodo del reporte")


class ReporteMensual(ReporteBase):
    # PLANTILLA BASE PARA UN REPORTE MENSUAL DE INGRESOS.

    def __init__(self) -> None:
        super().__init__(
            tipo="Mensual",
            titulo="Reporte mensual de ingresos",
        )


class ReporteTrimestral(ReporteBase):
    # PLANTILLA BASE PARA UN REPORTE TRIMESTRAL FINANCIERO.

    def __init__(self) -> None:
        super().__init__(
            tipo="Trimestral",
            titulo="Reporte trimestral de gastos e ingresos",
        )


class ReporteAnual(ReporteBase):
    # PLANTILLA BASE PARA UN REPORTE ANUAL CONSOLIDADO.

    def __init__(self) -> None:
        super().__init__(
            tipo="Anual",
            titulo="Reporte anual consolidado",
        )


def crear_catalogo_plantillas() -> dict[str, ReporteBase]:
    # CREA EL CATALOGO PEQUENO REQUERIDO POR EL FLUJO DE REPORTES.

    return {
        "mensual": ReporteMensual(),
        "trimestral": ReporteTrimestral(),
        "anual": ReporteAnual(),
    }

