# PROCESO DE MANTENIMIENTO Y CONSULTA DE TIPOS DE CAMBIO.

from datetime import date

from aplicacion.configuracion.configuracion_global import ConfiguracionGlobal
from aplicacion.dominio.entidades.tipo_cambio import TipoCambio
from aplicacion.persistencia.repositorios.repositorio_tipos_cambio import (
    RepositorioTiposCambio,
)
from aplicacion.servicios.utilidades import convertir_fecha, obtener_requerido


class ServicioTiposCambio:
    # MANTIENE MYSQL Y CONFIGURACIONGLOBAL CON LAS MISMAS TASAS ACTIVAS.

    def __init__(
        self,
        repositorio: RepositorioTiposCambio,
        configuracion: ConfiguracionGlobal,
    ) -> None:
        self._repositorio = repositorio
        self._configuracion = configuracion

    def listar(self) -> list[TipoCambio]:
        # DEVUELVE EL HISTORIAL DE TASAS REGISTRADAS.

        return self._repositorio.listar()

    def cargar_tasas_activas(self) -> None:
        # CARGA UNA SOLA VEZ LAS TASAS VIGENTES DESDE MYSQL AL SINGLETON.

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
        # BUSCA LA TASA APLICABLE O INFORMA QUE FALTA CONFIGURARLA.

        tipo_cambio = self._repositorio.obtener_vigente(
            codigo_divisa,
            fecha_referencia,
        )
        if tipo_cambio is None:
            raise ValueError(f"No existe una tasa activa para {codigo_divisa}/EUR.")
        return tipo_cambio

    def registrar(self, datos: dict) -> TipoCambio:
        # REGISTRA UNA TASA NUEVA Y ACTUALIZA LA CONFIGURACION EN MEMORIA.

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

    def actualizar(self, id_tipo_cambio: int, datos: dict) -> TipoCambio:
        # ACTUALIZA UNA TASA GUARDANDO SU IDENTIFICADOR E HISTORIAL.

        actual = self._repositorio.obtener_por_id(id_tipo_cambio)
        if actual is None:
            raise ValueError("El tipo de cambio indicado no existe.")
        tipo_cambio = TipoCambio(
            codigo_divisa_origen=str(
                obtener_requerido(datos, "codigo_divisa_origen")
            ),
            tasa=obtener_requerido(datos, "tasa"),
            fecha_vigencia=convertir_fecha(
                obtener_requerido(datos, "fecha_vigencia"),
                "fecha_vigencia",
            ),
            activa=actual.activa,
            id_tipo_cambio=id_tipo_cambio,
        )
        self._repositorio.actualizar(tipo_cambio)
        if actual.activa and actual.codigo_divisa_origen != tipo_cambio.codigo_divisa_origen:
            self._configuracion.eliminar_tasa(actual.codigo_divisa_origen)
        if tipo_cambio.activa:
            self._configuracion.actualizar_tasa(
                tipo_cambio.codigo_divisa_origen,
                tipo_cambio.tasa,
            )
        return tipo_cambio

    def desactivar(self, id_tipo_cambio: int) -> TipoCambio:
        # DESACTIVA UNA TASA NO CORPORATIVA Y GUARDA EL HISTORIAL.

        tipo_cambio = self._repositorio.obtener_por_id(id_tipo_cambio)
        if tipo_cambio is None or not tipo_cambio.activa:
            raise ValueError("La tasa indicada no existe o ya esta inactiva.")
        if tipo_cambio.codigo_divisa_origen == "EUR":
            raise ValueError("La tasa EUR/EUR es obligatoria y no puede eliminarse.")
        self._repositorio.desactivar(id_tipo_cambio)
        self._configuracion.eliminar_tasa(tipo_cambio.codigo_divisa_origen)
        tipo_cambio.activa = False
        return tipo_cambio

