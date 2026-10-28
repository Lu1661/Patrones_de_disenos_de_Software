# ACCESO SIMPLIFICADO A LA GENERACION DE REPORTES SERF.

from aplicacion.configuracion.configuracion_global import ConfiguracionGlobal
from aplicacion.dominio.contratos.contrato_reporte import IReporteFinanciero
from aplicacion.dominio.validaciones import limpiar_texto
from aplicacion.reportes.constructor_reporte import (
    DirectorReporte,
    ReporteFinancieroBuilder,
)
from aplicacion.reportes.estructura_reporte import ComponenteReporte
from aplicacion.reportes.modelos_reporte import (
    ReporteBase,
    crear_catalogo_plantillas,
)
from aplicacion.reportes.personalizacion_reporte import (
    FirmaDigitalDecorator,
    MarcaDeAguaDecorator,
)


class FachadaSERF:
    # COORDINA LOS PATRONES REQUERIDOS MEDIANTE UNA OPERACION SENCILLA.

    def __init__(
        self,
        configuracion: ConfiguracionGlobal | None = None,
        director: DirectorReporte | None = None,
        plantillas: dict[str, ReporteBase] | None = None,
    ) -> None:
        self._configuracion = configuracion or ConfiguracionGlobal.obtener_instancia()
        self._director = director or DirectorReporte(ReporteFinancieroBuilder())
        self._plantillas = plantillas or crear_catalogo_plantillas()

    def emitir_reporte_consolidado(
        self,
        tipo: str,
        periodo: str,
        secciones: ComponenteReporte,
        *,
        con_marca_agua: bool = False,
        con_firma: bool = False,
        graficos: list[str] | None = None,
        conclusiones: list[str] | None = None,
    ) -> str:
        # ============================================================
        # PATRON FACADE: GENERACION UNIFICADA DEL REPORTE
        # Este bloque coordina Prototype, Builder, Composite y Decorator
        # sin exponer esas operaciones a la futura interfaz web.
        # Cumple: RF-09 y CU-06.
        # ============================================================
        tipo_normalizado = limpiar_texto(tipo, "tipo de reporte").lower()
        periodo_normalizado = limpiar_texto(periodo, "periodo")
        if tipo_normalizado not in self._plantillas:
            opciones = ", ".join(self._plantillas)
            raise ValueError(f"El tipo de reporte debe ser: {opciones}.")
        if not isinstance(secciones, ComponenteReporte):
            raise ValueError("Las secciones del reporte no son validas.")
        if not isinstance(con_marca_agua, bool) or not isinstance(con_firma, bool):
            raise ValueError("Las opciones de seguridad deben ser verdaderas o falsas.")

        plantilla_clonada = self._plantillas[tipo_normalizado].clonar()
        reporte = self._director.construir_reporte_completo(
            plantilla_clonada,
            periodo_normalizado,
            secciones,
            graficos,
            conclusiones,
        )

        reporte_final: IReporteFinanciero = reporte
        if con_marca_agua:
            reporte_final = MarcaDeAguaDecorator(reporte_final)
        if con_firma:
            reporte_final = FirmaDigitalDecorator(reporte_final)

        return reporte_final.emitir()

