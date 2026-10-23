"""Proceso de registro atomico de ventas."""

from datetime import date

from aplicacion.dominio.entidades.detalle_venta import DetalleVenta
from aplicacion.dominio.entidades.transaccion_venta import TransaccionVenta
from aplicacion.persistencia.conexion.conexion_mysql import ConexionMySQL
from aplicacion.persistencia.repositorios.repositorio_filiales import (
    RepositorioFiliales,
)
from aplicacion.persistencia.repositorios.repositorio_inventario import (
    RepositorioInventario,
)
from aplicacion.persistencia.repositorios.repositorio_productos import (
    RepositorioProductos,
)
from aplicacion.persistencia.repositorios.repositorio_tipos_cambio import (
    RepositorioTiposCambio,
)
from aplicacion.persistencia.repositorios.repositorio_ventas import (
    RepositorioVentas,
)
from aplicacion.servicios.utilidades import (
    convertir_entero,
    convertir_fecha_hora,
    obtener_requerido,
)


class ServicioVentas:
    """Coordina stock, conversion y comprobante dentro de una transaccion."""

    def __init__(
        self,
        administrador_conexion: ConexionMySQL,
        repositorio_ventas: RepositorioVentas,
        repositorio_inventario: RepositorioInventario,
        repositorio_productos: RepositorioProductos,
        repositorio_filiales: RepositorioFiliales,
        repositorio_tasas: RepositorioTiposCambio,
    ) -> None:
        self._administrador_conexion = administrador_conexion
        self._repositorio_ventas = repositorio_ventas
        self._repositorio_inventario = repositorio_inventario
        self._repositorio_productos = repositorio_productos
        self._repositorio_filiales = repositorio_filiales
        self._repositorio_tasas = repositorio_tasas

    def registrar(self, datos: dict) -> TransaccionVenta:
        """Registra una venta o revierte todo si falla una parte."""

        # ============================================================
        # BLOQUE: REGISTRO ATOMICO DE UNA VENTA
        # Este bloque bloquea el inventario, descuenta las existencias y
        # guarda el comprobante usando la misma transaccion de MySQL.
        # Cumple: RF-02, RF-03, RF-04, CU-02, CU-03 y CU-04.
        # ============================================================
        id_filial = convertir_entero(
            obtener_requerido(datos, "id_filial"),
            "id_filial",
        )
        id_producto = convertir_entero(
            obtener_requerido(datos, "id_producto"),
            "id_producto",
        )
        cantidad = convertir_entero(
            obtener_requerido(datos, "cantidad"),
            "cantidad",
        )
        fecha_venta = convertir_fecha_hora(
            obtener_requerido(datos, "fecha_venta"),
            "fecha_venta",
        )

        filial = self._repositorio_filiales.obtener_por_id(id_filial)
        if filial is None or not filial.activa:
            raise ValueError("La filial indicada no existe o esta inactiva.")

        producto = self._repositorio_productos.obtener_por_id(id_producto)
        if producto is None or not producto.activo:
            raise ValueError("El producto indicado no existe o esta inactivo.")

        tipo_cambio = self._repositorio_tasas.obtener_vigente(
            filial.codigo_divisa,
            fecha_venta.date(),
        )
        if tipo_cambio is None:
            raise ValueError(
                f"No existe una tasa activa para {filial.codigo_divisa}/EUR."
            )

        with self._administrador_conexion.transaccion() as conexion:
            inventario = self._repositorio_inventario.obtener(
                id_filial,
                id_producto,
                bloquear=True,
                conexion=conexion,
            )
            if inventario is None:
                raise ValueError("El producto no existe en el inventario de la filial.")

            # ============================================================
            # BLOQUE: VALIDACION DEL STOCK ANTES DE REGISTRAR LA VENTA
            # Este bloque informa al usuario cuantas unidades hay disponibles
            # y evita crear una venta que deje el inventario en negativo.
            # Cumple: RF-03 y CU-03.
            # ============================================================
            if not inventario.tiene_stock(cantidad):
                raise ValueError(
                    "Stock insuficiente. "
                    f"Disponible: {inventario.stock_disponible}."
                )

            precio_recibido = datos.get("precio_unitario_local")
            precio = (
                precio_recibido
                if precio_recibido not in (None, "")
                else inventario.precio_venta_local
            )
            detalle = DetalleVenta(
                id_producto=id_producto,
                cantidad=cantidad,
                precio_unitario_local=precio,
                costo_unitario_eur=producto.costo_unitario_eur,
            )
            venta = TransaccionVenta(
                numero_factura=str(
                    obtener_requerido(datos, "numero_factura")
                ),
                id_filial=id_filial,
                fecha_venta=fecha_venta,
                cliente=str(obtener_requerido(datos, "cliente")),
                vendedor=str(obtener_requerido(datos, "vendedor")),
                metodo_pago=str(obtener_requerido(datos, "metodo_pago")),
                codigo_divisa=filial.codigo_divisa,
                tasa_eur_aplicada=tipo_cambio.tasa,
                detalles=[detalle],
            )

            self._repositorio_inventario.descontar_stock(
                id_filial,
                id_producto,
                cantidad,
                conexion,
            )
            self._repositorio_ventas.registrar(venta, conexion)

        return venta

    def listar_por_periodo(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        id_filial: int | None = None,
    ) -> list[TransaccionVenta]:
        """Retorna las ventas que utilizaran las consultas y reportes."""

        if fecha_inicio > fecha_fin:
            raise ValueError("La fecha inicial no puede superar la fecha final.")
        return self._repositorio_ventas.listar_por_periodo(
            fecha_inicio,
            fecha_fin,
            id_filial,
        )

