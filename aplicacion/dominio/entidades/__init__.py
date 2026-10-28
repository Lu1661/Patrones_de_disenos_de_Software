# ENTIDADES PRINCIPALES DEL DOMINIO FINANCIERO.

from aplicacion.dominio.entidades.detalle_venta import DetalleVenta
from aplicacion.dominio.entidades.divisa import Divisa
from aplicacion.dominio.entidades.filial import Filial
from aplicacion.dominio.entidades.inventario_filial import InventarioFilial
from aplicacion.dominio.entidades.producto_importado import ProductoImportado
from aplicacion.dominio.entidades.tipo_cambio import TipoCambio
from aplicacion.dominio.entidades.transaccion_venta import TransaccionVenta


__all__ = [
    "DetalleVenta",
    "Divisa",
    "Filial",
    "InventarioFilial",
    "ProductoImportado",
    "TipoCambio",
    "TransaccionVenta",
]

