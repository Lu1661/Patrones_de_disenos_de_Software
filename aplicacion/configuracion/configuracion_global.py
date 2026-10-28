# CONFIGURACION CORPORATIVA COMPARTIDA POR LOS PROCESOS DEL NEGOCIO.

from decimal import Decimal
from threading import Lock

from aplicacion.dominio.validaciones import (
    normalizar_codigo_iso,
    redondear_moneda,
    redondear_tasa,
    validar_decimal_no_negativo,
)


class ConfiguracionGlobal:
    # MANTIENE UNA SOLA CONFIGURACION CAMBIARIA DURANTE LA EJECUCION.

    _instancia: "ConfiguracionGlobal | None" = None
    _bloqueo = Lock()

    def __new__(cls) -> "ConfiguracionGlobal":
        # ============================================================
        # PATRON SINGLETON: INSTANCIA UNICA DE CONFIGURACION
        # Este bloque impide que distintas partes del sistema manejen
        # tasas o reglas que lo contradigan.
        # Cumple: RF-04, CU-04 y CU-05.
        # ============================================================
        if cls._instancia is None:
            with cls._bloqueo:
                if cls._instancia is None:
                    cls._instancia = super().__new__(cls)
        return cls._instancia

    def __init__(self) -> None:
        if getattr(self, "_inicializada", False):
            return

        self.moneda_corporativa = "EUR"
        self.formato_fecha = "%Y-%m-%d"
        self._tasas_cambio: dict[str, Decimal] = {
            "EUR": Decimal("1.00000000")
        }
        self._inicializada = True

    @classmethod
    def obtener_instancia(cls) -> "ConfiguracionGlobal":
        # DEVUELVE LA INSTANCIA UNICA.

        return cls()

    def actualizar_tasa(
        self,
        codigo_divisa_origen: str,
        nueva_tasa: Decimal | str | int,
    ) -> None:
        # REGISTRA EN MEMORIA UNA TASA VIGENTE HACIA EUR.

        codigo = normalizar_codigo_iso(codigo_divisa_origen)
        tasa = redondear_tasa(nueva_tasa)
        if codigo == "EUR" and tasa != Decimal("1.00000000"):
            raise ValueError("La tasa EUR hacia EUR debe ser igual a 1.")
        self._tasas_cambio[codigo] = tasa

    def eliminar_tasa(self, codigo_divisa_origen: str) -> None:
        # RETIRA DE MEMORIA UNA TASA INACTIVA SIN ELIMINAR LA BASE EUR.

        codigo = normalizar_codigo_iso(codigo_divisa_origen)
        if codigo != "EUR":
            self._tasas_cambio.pop(codigo, None)

    def obtener_tasa(self, codigo_divisa_origen: str) -> Decimal:
        # BUSCA UNA TASA REGISTRADA O INFORMA QUE DEBE CONFIGURARSE.

        codigo = normalizar_codigo_iso(codigo_divisa_origen)
        if codigo not in self._tasas_cambio:
            raise ValueError(f"No existe una tasa activa para {codigo}/EUR.")
        return self._tasas_cambio[codigo]

    def convertir_a_eur(
        self,
        monto: Decimal | str | int,
        codigo_divisa_origen: str,
    ) -> Decimal:
        # CONVIERTE UN IMPORTE CON LA TASA CENTRALIZADA VIGENTE.

        importe = validar_decimal_no_negativo(monto, "monto a convertir")
        tasa = self.obtener_tasa(codigo_divisa_origen)
        return redondear_moneda(importe * tasa)

    def listar_tasas(self) -> dict[str, Decimal]:
        # ENTREGA UNA COPIA PARA IMPEDIR MODIFICACIONES EXTERNAS DIRECTAS.

        return self._tasas_cambio.copy()

