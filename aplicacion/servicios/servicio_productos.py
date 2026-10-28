# PROCESO DE REGISTRO Y CONSULTA DE PRODUCTOS IMPORTADOS.

from aplicacion.dominio.entidades.inventario_filial import InventarioFilial
from aplicacion.dominio.entidades.producto_importado import ProductoImportado
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
from aplicacion.servicios.utilidades import (
    convertir_entero,
    convertir_fecha,
    obtener_requerido,
)


class ServicioProductos:
    # REGISTRA EL PRODUCTO Y SU STOCK INICIAL COMO UNA SOLA OPERACION.

    def __init__(
        self,
        administrador_conexion: ConexionMySQL,
        repositorio_productos: RepositorioProductos,
        repositorio_inventario: RepositorioInventario,
        repositorio_filiales: RepositorioFiliales,
        repositorio_tasas: RepositorioTiposCambio,
    ) -> None:
        self._administrador_conexion = administrador_conexion
        self._repositorio_productos = repositorio_productos
        self._repositorio_inventario = repositorio_inventario
        self._repositorio_filiales = repositorio_filiales
        self._repositorio_tasas = repositorio_tasas

    def listar(self) -> list[ProductoImportado]:
        # DEVUELVE TODOS LOS PRODUCTOS REGISTRADOS.

        return self._repositorio_productos.listar()

    def registrar_con_stock(self, datos: dict) -> tuple[ProductoImportado, InventarioFilial]:
        # REGISTRA PRODUCTO E INVENTARIO SIN DEJAR DATOS PARCIALES.

        # ============================================================
        # BLOQUE: REGISTRO ATOMICO DEL PRODUCTO IMPORTADO
        # Este bloque valida la filial y la tasa CNY/EUR, luego guarda
        # el producto y su stock inicial dentro de una transaccion.
        # Cumple: RF-01, CU-01 y CU-04.
        # ============================================================
        id_filial = convertir_entero(
            obtener_requerido(datos, "id_filial"),
            "id_filial",
        )
        filial = self._repositorio_filiales.obtener_por_id(id_filial)
        if filial is None or not filial.activa:
            raise ValueError("La filial indicada no existe o esta inactiva.")

        fecha_importacion = convertir_fecha(
            obtener_requerido(datos, "fecha_importacion"),
            "fecha_importacion",
        )
        tasa_cny = self._repositorio_tasas.obtener_vigente(
            "CNY",
            fecha_importacion,
        )
        if tasa_cny is None:
            raise ValueError("No existe una tasa activa para CNY/EUR.")

        producto = ProductoImportado.crear_con_conversion(
            codigo=str(obtener_requerido(datos, "codigo")),
            nombre=str(obtener_requerido(datos, "nombre")),
            descripcion_tecnica=str(
                obtener_requerido(datos, "descripcion_tecnica")
            ),
            categoria=str(obtener_requerido(datos, "categoria")),
            costo_unitario_cny=obtener_requerido(datos, "costo_unitario_cny"),
            tasa_cny_eur=tasa_cny.tasa,
            proveedor=str(obtener_requerido(datos, "proveedor")),
            fecha_importacion=fecha_importacion,
        )

        stock_inicial = convertir_entero(
            obtener_requerido(datos, "stock_inicial"),
            "stock_inicial",
        )

        with self._administrador_conexion.transaccion() as conexion:
            self._repositorio_productos.crear(producto, conexion)
            inventario = InventarioFilial(
                id_filial=id_filial,
                id_producto=producto.id_producto,
                stock_disponible=stock_inicial,
                precio_venta_local=obtener_requerido(
                    datos,
                    "precio_venta_local",
                ),
            )
            self._repositorio_inventario.crear(inventario, conexion)

        return producto, inventario

    def actualizar(self, id_producto: int, datos: dict) -> ProductoImportado:
        # ACTUALIZA EL CATALOGO SIN MODIFICAR STOCK NI PRECIOS LOCALES.

        actual = self._repositorio_productos.obtener_por_id(id_producto)
        if actual is None:
            raise ValueError("El producto indicado no existe.")
        fecha_importacion = convertir_fecha(
            obtener_requerido(datos, "fecha_importacion"),
            "fecha_importacion",
        )
        tasa_cny = self._repositorio_tasas.obtener_vigente(
            "CNY",
            fecha_importacion,
        )
        if tasa_cny is None:
            raise ValueError("No existe una tasa activa para CNY/EUR.")
        producto = ProductoImportado.crear_con_conversion(
            codigo=str(obtener_requerido(datos, "codigo")),
            nombre=str(obtener_requerido(datos, "nombre")),
            descripcion_tecnica=str(
                obtener_requerido(datos, "descripcion_tecnica")
            ),
            categoria=str(obtener_requerido(datos, "categoria")),
            costo_unitario_cny=obtener_requerido(datos, "costo_unitario_cny"),
            tasa_cny_eur=tasa_cny.tasa,
            proveedor=str(obtener_requerido(datos, "proveedor")),
            fecha_importacion=fecha_importacion,
        )
        producto.id_producto = id_producto
        producto.activo = actual.activo
        self._repositorio_productos.actualizar(producto)
        return producto

    def desactivar(self, id_producto: int) -> ProductoImportado:
        # DESACTIVA UN PRODUCTO SIN BORRAR INVENTARIOS NI VENTAS.

        producto = self._repositorio_productos.obtener_por_id(id_producto)
        if producto is None or not producto.activo:
            raise ValueError("El producto indicado no existe o ya esta inactivo.")
        self._repositorio_productos.desactivar(id_producto)
        producto.activo = False
        return producto

