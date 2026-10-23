"""Entidad que representa una tasa de conversion hacia EUR."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from aplicacion.dominio.validaciones import (
    normalizar_codigo_iso,
    redondear_moneda,
    redondear_tasa,
    validar_decimal_no_negativo,
    validar_fecha_no_futura,
    validar_id_opcional,
)


@dataclass
class TipoCambio:
    """Tasa historica que convierte una divisa de origen hacia EUR."""

    codigo_divisa_origen: str
    tasa: Decimal
    fecha_vigencia: date
    codigo_divisa_destino: str = "EUR"
    activa: bool = True
    id_tipo_cambio: int | None = None

    def __post_init__(self) -> None:
        # ============================================================
        # BLOQUE: VALIDACION DE LA TASA DE CAMBIO
        # Este bloque limita la conversion a la moneda corporativa EUR
        # y conserva ocho decimales para evitar perdida de precision.
        # Cumple: RF-04, CU-04 y CU-05.
        # ============================================================
        self.codigo_divisa_origen = normalizar_codigo_iso(
            self.codigo_divisa_origen
        )
        self.codigo_divisa_destino = normalizar_codigo_iso(
            self.codigo_divisa_destino
        )
        if self.codigo_divisa_destino != "EUR":
            raise ValueError("La divisa de destino debe ser EUR.")

        self.tasa = redondear_tasa(self.tasa)
        self.fecha_vigencia = validar_fecha_no_futura(
            self.fecha_vigencia,
            "fecha de vigencia",
        )
        self.id_tipo_cambio = validar_id_opcional(
            self.id_tipo_cambio,
            "id de tipo de cambio",
        )

        if not isinstance(self.activa, bool):
            raise ValueError("El estado del tipo de cambio debe ser verdadero o falso.")
        if self.codigo_divisa_origen == "EUR" and self.tasa != Decimal("1.00000000"):
            raise ValueError("La tasa EUR hacia EUR debe ser igual a 1.")

    def convertir_a_eur(self, monto: Decimal | str | int) -> Decimal:
        """Convierte un importe no negativo utilizando la tasa registrada."""

        importe = validar_decimal_no_negativo(monto, "monto a convertir")
        return redondear_moneda(importe * self.tasa)

