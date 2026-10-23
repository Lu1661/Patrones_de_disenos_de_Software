"""Configuracion corporativa compartida por los procesos del negocio."""

from decimal import Decimal
from threading import Lock

from aplicacion.dominio.validaciones import (
    normalizar_codigo_iso,
    redondear_moneda,
    redondear_tasa,
    validar_decimal_no_negativo,
)


class ConfiguracionGlobal:
    """Mantiene una sola configuracion cambiaria durante la ejecucion."""

    _instancia: "ConfiguracionGlobal | None" = None
    _bloqueo = Lock()

    def __new__(cls) -> "ConfiguracionGlobal":
        # ============================================================
        # PATRON SINGLETON: INSTANCIA UNICA DE CONFIGURACION
        # Este bloque impide que distintas partes del sistema manejen
        # tasas o reglas de redondeo contradictorias.
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
        """Retorna la instancia unica usando un nombre facil de exponer."""

        return cls()

    def actualizar_tasa(
        self,
        codigo_divisa_origen: str,
        nueva_tasa: Decimal | str | int,
    ) -> None:
        """Registra en memoria una tasa vigente hacia EUR."""

        codigo = normalizar_codigo_iso(codigo_divisa_origen)
        tasa = redondear_tasa(nueva_tasa)
        if codigo == "EUR" and tasa != Decimal("1.00000000"):
            raise ValueError("La tasa EUR hacia EUR debe ser igual a 1.")
        self._tasas_cambio[codigo] = tasa

    def obtener_tasa(self, codigo_divisa_origen: str) -> Decimal:
        """Obtiene una tasa registrada o informa que debe configurarse."""

        codigo = normalizar_codigo_iso(codigo_divisa_origen)
        if codigo not in self._tasas_cambio:
            raise ValueError(f"No existe una tasa activa para {codigo}/EUR.")
        return self._tasas_cambio[codigo]

    def convertir_a_eur(
        self,
        monto: Decimal | str | int,
        codigo_divisa_origen: str,
    ) -> Decimal:
        """Convierte un importe con la tasa centralizada vigente."""

        importe = validar_decimal_no_negativo(monto, "monto a convertir")
        tasa = self.obtener_tasa(codigo_divisa_origen)
        return redondear_moneda(importe * tasa)

    def listar_tasas(self) -> dict[str, Decimal]:
        """Entrega una copia para impedir modificaciones externas directas."""

        return self._tasas_cambio.copy()

