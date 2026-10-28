# ENTIDAD QUE RELACIONA UN PRODUCTO CON EL INVENTARIO DE UNA FILIAL.

from dataclasses import dataclass
from decimal import Decimal

from aplicacion.dominio.validaciones import (
    redondear_moneda,
    validar_decimal_positivo,
    validar_entero_no_negativo,
    validar_entero_positivo,
    validar_id_opcional,
)


@dataclass
class InventarioFilial:
    # EXISTENCIAS Y PRECIO LOCAL DE UN PRODUCTO EN UNA FILIAL.

    id_filial: int
    id_producto: int
    stock_disponible: int
    precio_venta_local: Decimal
    id_inventario: int | None = None

    def __post_init__(self) -> None:
        # ============================================================
        # BLOQUE: VALIDACION DEL INVENTARIO LOCAL
        # Este bloque garantiza que el stock inicial no sea negativo
        # y que el producto tenga un precio valido en su filial.
        # Cumple: RF-01, RF-03, CU-01 y CU-03.
        # ============================================================
        self.id_filial = validar_entero_positivo(self.id_filial, "id de filial")
        self.id_producto = validar_entero_positivo(
            self.id_producto,
            "id de producto",
        )
        self.stock_disponible = validar_entero_no_negativo(
            self.stock_disponible,
            "stock disponible",
        )
        self.precio_venta_local = redondear_moneda(
            validar_decimal_positivo(
                self.precio_venta_local,
                "precio de venta local",
            )
        )
        self.id_inventario = validar_id_opcional(
            self.id_inventario,
            "id de inventario",
        )

    def tiene_stock(self, cantidad: int) -> bool:
        # INDICA SI EXISTEN UNIDADES SUFICIENTES PARA UNA VENTA.

        unidades = validar_entero_positivo(cantidad, "cantidad solicitada")
        return self.stock_disponible >= unidades

    def descontar_stock(self, cantidad: int) -> None:
        # DESCUENTA UNIDADES SIN PERMITIR QUE EL INVENTARIO QUEDE NEGATIVO.

        # ============================================================
        # BLOQUE: DESCUENTO DE EXISTENCIAS
        # Este bloque valida el saldo y evita confirmar ventas que no
        # cuentan con unidades fisicas suficientes en la filial.
        # Cumple: RF-03 y CU-03.
        # ============================================================
        unidades = validar_entero_positivo(cantidad, "cantidad a descontar")
        if not self.tiene_stock(unidades):
            raise ValueError(
                f"Stock insuficiente. Disponible: {self.stock_disponible}."
            )
        self.stock_disponible -= unidades

    def reponer_stock(self, cantidad: int) -> None:
        # INCREMENTA LAS EXISTENCIAS POR UNA NUEVA RECEPCION O UNA REVERSION.

        unidades = validar_entero_positivo(cantidad, "cantidad a reponer")
        self.stock_disponible += unidades

