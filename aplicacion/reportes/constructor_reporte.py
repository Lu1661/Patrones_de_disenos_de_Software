# CONSTRUCCION ORDENADA DE LOS REPORTES FINANCIEROS.

from aplicacion.dominio.contratos.contrato_reporte import IReporteBuilder
from aplicacion.dominio.validaciones import limpiar_texto
from aplicacion.reportes.estructura_reporte import ComponenteReporte
from aplicacion.reportes.modelos_reporte import ReporteBase


class ReporteFinancieroBuilder(IReporteBuilder):
    # CONSTRUYE UN REPORTE POR PASOS SIN MEZCLAR LA OBTENCION DE DATOS.

    def __init__(self) -> None:
        self._reporte_actual = ReporteBase()

    def reset(self, reporte_inicial: ReporteBase | None = None) -> None:
        # ============================================================
        # PATRON BUILDER: INICIO DE LA CONSTRUCCION
        # Este bloque prepara un reporte limpio a partir de la plantilla
        # clonada antes de incorporar encabezado, cuerpo y conclusiones.
        # Cumple: RF-06 y CU-08.
        # ============================================================
        self._reporte_actual = reporte_inicial or ReporteBase()

    def definir_encabezado(self, titulo: str, periodo: str) -> None:
        # COLOCA LOS DATOS VISIBLES QUE IDENTIFICAN EL REPORTE.

        self._reporte_actual.definir_datos_principales(titulo, periodo)

    def construir_cuerpo_consolidado(
        self,
        secciones: ComponenteReporte,
    ) -> None:
        # ASIGNA EL ARBOL PREVIAMENTE CONSTRUIDO POR EL COMPOSITE.

        if not isinstance(secciones, ComponenteReporte):
            raise ValueError("El cuerpo debe ser un componente de reporte.")
        self._reporte_actual.cuerpo = secciones

    def agregar_graficos(self, graficos: list[str]) -> None:
        # AGREGA DESCRIPCIONES QUE LUEGO REPRESENTARA LA INTERFAZ WEB.

        self._reporte_actual.graficos = [
            limpiar_texto(grafico, "grafico") for grafico in graficos
        ]

    def agregar_conclusiones(self, conclusiones: list[str]) -> None:
        # AGREGA CONCLUSIONES SENCILLAS CALCULADAS PARA EL PERIODO.

        self._reporte_actual.conclusiones = [
            limpiar_texto(conclusion, "conclusion")
            for conclusion in conclusiones
        ]

    def agregar_totales(self) -> None:
        # CALCULA EL TOTAL UTILIZANDO EL CONTRATO COMUN DEL COMPOSITE.

        self._reporte_actual.total_eur = (
            self._reporte_actual.cuerpo.calcular_total_eur()
        )

    def obtener_resultado(self) -> ReporteBase:
        # ENTREGA EL REPORTE COMPLETO Y PREPARA UN NUEVO CICLO.

        resultado = self._reporte_actual
        self.reset()
        return resultado


class DirectorReporte:
    # DEFINE EL ORDEN UNICO DE LOS PASOS USADOS PARA CREAR UN REPORTE.

    def __init__(self, builder: IReporteBuilder) -> None:
        self._builder = builder

    def establecer_builder(self, builder: IReporteBuilder) -> None:
        # PERMITE UTILIZAR OTRO CONSTRUCTOR QUE RESPETE EL MISMO CONTRATO.

        self._builder = builder

    def construir_reporte_completo(
        self,
        plantilla_clonada: ReporteBase,
        periodo: str,
        secciones: ComponenteReporte,
        graficos: list[str] | None = None,
        conclusiones: list[str] | None = None,
    ) -> ReporteBase:
        # EJECUTA EN ORDEN LOS PASOS DE CONSTRUCCION SOLICITADOS.

        self._builder.reset(plantilla_clonada)
        self._builder.definir_encabezado(
            plantilla_clonada.titulo,
            periodo,
        )
        self._builder.construir_cuerpo_consolidado(secciones)
        self._builder.agregar_graficos(graficos or [])
        self._builder.agregar_conclusiones(conclusiones or [])
        self._builder.agregar_totales()
        resultado = self._builder.obtener_resultado()

        if not isinstance(resultado, ReporteBase):
            raise ValueError("El constructor no entrego un reporte valido.")
        return resultado

