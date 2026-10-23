"""Entidad que representa un producto incluido en una venta."""

from dataclasses import dataclass
from decimal import Decimal

from aplicacion.dominio.validaciones import (
    redondear_moneda,
    validar_decimal_positivo,
    validar_entero_positivo,
    validar_id_opcional,
)


@dataclass
class DetalleVenta:
    """Producto, cantidad, precio y costo historico de una venta."""

    id_producto: int
    cantidad: int
    precio_unitario_local: Decimal
    costo_unitario_eur: Decimal
    id_detalle: int | None = None

    def __post_init__(self) -> None:
        # ============================================================
        # BLOQUE: VALIDACION DEL DETALLE DE VENTA
        # Este bloque conserva el precio y costo usados en la fecha de
        # la venta para que los reportes historicos no cambien despues.
        # Cumple: RF-02 y CU-02.
        # ============================================================
        self.id_producto = validar_entero_positivo(
            self.id_producto,
            "id de producto",
        )
        self.cantidad = validar_entero_positivo(self.cantidad, "cantidad")
        self.precio_unitario_local = redondear_moneda(
            validar_decimal_positivo(
                self.precio_unitario_local,
                "precio unitario local",
            )
        )
        self.costo_unitario_eur = redondear_moneda(
            validar_decimal_positivo(
                self.costo_unitario_eur,
                "costo unitario EUR",
            )
        )
        self.id_detalle = validar_id_opcional(self.id_detalle, "id de detalle")

    @property
    def subtotal_local(self) -> Decimal:
        """Calcula el importe local correspondiente al detalle."""

        return redondear_moneda(self.precio_unitario_local * self.cantidad)

    @property
    def subtotal_costo_eur(self) -> Decimal:
        """Calcula el gasto de importacion correspondiente al detalle."""

        return redondear_moneda(self.costo_unitario_eur * self.cantidad)

