# ENTIDAD QUE REPRESENTA UN PRODUCTO TECNOLOGICO IMPORTADO.

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from aplicacion.dominio.validaciones import (
    limpiar_texto,
    redondear_moneda,
    redondear_tasa,
    validar_decimal_positivo,
    validar_fecha_no_futura,
    validar_id_opcional,
)


@dataclass
class ProductoImportado:
    # PRODUCTO TECNOLOGICO COMPRADO EN CNY Y VALORIZADO EN EUR.

    codigo: str
    nombre: str
    descripcion_tecnica: str
    categoria: str
    costo_unitario_cny: Decimal
    costo_unitario_eur: Decimal
    proveedor: str
    fecha_importacion: date
    activo: bool = True
    id_producto: int | None = None

    def __post_init__(self) -> None:
        # ============================================================
        # BLOQUE: VALIDACION DEL PRODUCTO IMPORTADO
        # Este bloque comprueba los datos tecnicos y los costos antes
        # de que el producto pueda asignarse al inventario de una filial.
        # Cumple: RF-01 y CU-01.
        # ============================================================
        self.codigo = limpiar_texto(self.codigo, "codigo").upper()
        self.nombre = limpiar_texto(self.nombre, "nombre del producto")
        self.descripcion_tecnica = limpiar_texto(
            self.descripcion_tecnica,
            "descripcion tecnica",
        )
        self.categoria = limpiar_texto(self.categoria, "categoria")
        if len(self.categoria) > 50:
            raise ValueError("La categoria no puede superar 50 caracteres.")
        self.costo_unitario_cny = redondear_moneda(
            validar_decimal_positivo(self.costo_unitario_cny, "costo en CNY")
        )
        self.costo_unitario_eur = redondear_moneda(
            validar_decimal_positivo(self.costo_unitario_eur, "costo en EUR")
        )
        self.proveedor = limpiar_texto(self.proveedor, "proveedor")
        self.fecha_importacion = validar_fecha_no_futura(
            self.fecha_importacion,
            "fecha de importacion",
        )
        self.id_producto = validar_id_opcional(self.id_producto, "id de producto")

        if not isinstance(self.activo, bool):
            raise ValueError("El estado del producto debe ser verdadero o falso.")

    @classmethod
    def crear_con_conversion(
        cls,
        *,
        codigo: str,
        nombre: str,
        descripcion_tecnica: str,
        categoria: str,
        costo_unitario_cny: Decimal | str | int,
        tasa_cny_eur: Decimal | str | int,
        proveedor: str,
        fecha_importacion: date,
    ) -> "ProductoImportado":
        # CREA UN PRODUCTO CALCULANDO SU COSTO CORPORATIVO EN EUR.

        costo_cny = validar_decimal_positivo(costo_unitario_cny, "costo en CNY")
        tasa = redondear_tasa(tasa_cny_eur)
        costo_eur = redondear_moneda(costo_cny * tasa)

        return cls(
            codigo=codigo,
            nombre=nombre,
            descripcion_tecnica=descripcion_tecnica,
            categoria=categoria,
            costo_unitario_cny=costo_cny,
            costo_unitario_eur=costo_eur,
            proveedor=proveedor,
            fecha_importacion=fecha_importacion,
        )

