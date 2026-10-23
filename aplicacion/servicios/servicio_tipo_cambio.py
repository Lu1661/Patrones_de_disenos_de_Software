"""Proceso de mantenimiento y consulta de tipos de cambio."""

from datetime import date

from aplicacion.configuracion.configuracion_global import ConfiguracionGlobal
from aplicacion.dominio.entidades.tipo_cambio import TipoCambio
from aplicacion.persistencia.repositorios.repositorio_tipos_cambio import (
    RepositorioTiposCambio,
)
from aplicacion.servicios.utilidades import convertir_fecha, obtener_requerido


class ServicioTiposCambio:
    """Mantiene MySQL y ConfiguracionGlobal con las mismas tasas activas."""

    def __init__(
        self,
        repositorio: RepositorioTiposCambio,
        configuracion: ConfiguracionGlobal,
    ) -> None:
        self._repositorio = repositorio
        self._configuracion = configuracion

    def listar(self) -> list[TipoCambio]:
        """Retorna el historial de tasas registradas."""

        return self._repositorio.listar()

    def cargar_tasas_activas(self) -> None:
        """Carga una sola vez las tasas vigentes desde MySQL al Singleton."""

        codigos_cargados: set[str] = set()
        for tipo_cambio in self._repositorio.listar():
            codigo = tipo_cambio.codigo_divisa_origen
            if tipo_cambio.activa and codigo not in codigos_cargados:
                self._configuracion.actualizar_tasa(codigo, tipo_cambio.tasa)
                codigos_cargados.add(codigo)

    def obtener_vigente(
        self,
        codigo_divisa: str,
        fecha_referencia: date | None = None,
    ) -> TipoCambio:
        """Obtiene la tasa aplicable o informa que falta configurarla."""

        tipo_cambio = self._repositorio.obtener_vigente(
            codigo_divisa,
            fecha_referencia,
        )
        if tipo_cambio is None:
            raise ValueError(f"No existe una tasa activa para {codigo_divisa}/EUR.")
        return tipo_cambio

    def registrar(self, datos: dict) -> TipoCambio:
        """Registra una tasa nueva y actualiza la configuracion en memoria."""

        tipo_cambio = TipoCambio(
            codigo_divisa_origen=str(
                obtener_requerido(datos, "codigo_divisa_origen")
            ),
            tasa=obtener_requerido(datos, "tasa"),
            fecha_vigencia=convertir_fecha(
                obtener_requerido(datos, "fecha_vigencia"),
                "fecha_vigencia",
            ),
        )
        self._repositorio.registrar(tipo_cambio)
        self._configuracion.actualizar_tasa(
            tipo_cambio.codigo_divisa_origen,
            tipo_cambio.tasa,
        )
        return tipo_cambio

