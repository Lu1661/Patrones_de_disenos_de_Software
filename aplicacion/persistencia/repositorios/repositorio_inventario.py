# PERSISTENCIA DEL INVENTARIO POR FILIAL.

from decimal import Decimal

from mysql.connector.abstracts import MySQLConnectionAbstract

from aplicacion.dominio.entidades.inventario_filial import InventarioFilial
from aplicacion.dominio.validaciones import (
    redondear_moneda,
    validar_decimal_positivo,
    validar_entero_positivo,
)
from aplicacion.persistencia.conexion.conexion_mysql import ConexionMySQL
from aplicacion.persistencia.repositorios.repositorio_base import RepositorioBase


class RepositorioInventario(RepositorioBase):
    # CONSULTA Y MODIFICA LAS EXISTENCIAS LOCALES DE LAS FILIALES.

    def __init__(self, administrador_conexion: ConexionMySQL) -> None:
        super().__init__(administrador_conexion)

    @staticmethod
    def _convertir_fila(fila: dict) -> InventarioFilial:
        return InventarioFilial(
            id_filial=fila["id_filial"],
            id_producto=fila["id_producto"],
            stock_disponible=fila["stock_disponible"],
            precio_venta_local=fila["precio_venta_local"],
            id_inventario=fila["id_inventario"],
        )

    def listar_por_filial(self, id_filial: int) -> list[InventarioFilial]:
        # LISTA LAS EXISTENCIAS DE UNA FILIAL.

        consulta = """
            SELECT id_inventario, id_filial, id_producto,
                   stock_disponible, precio_venta_local
            FROM inventarios_filial
            WHERE id_filial = %s
            ORDER BY id_producto
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta, (id_filial,))
                return [self._convertir_fila(fila) for fila in cursor.fetchall()]
            finally:
                cursor.close()

    def listar_todos(self) -> list[InventarioFilial]:
        # LISTA LOS PRECIOS Y EXISTENCIAS ASOCIADOS A TODOS LOS PRODUCTOS.

        consulta = """
            SELECT id_inventario, id_filial, id_producto,
                   stock_disponible, precio_venta_local
            FROM inventarios_filial
            ORDER BY id_producto, id_filial
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta)
                return [self._convertir_fila(fila) for fila in cursor.fetchall()]
            finally:
                cursor.close()

    def obtener(
        self,
        id_filial: int,
        id_producto: int,
        *,
        bloquear: bool = False,
        conexion: MySQLConnectionAbstract | None = None,
    ) -> InventarioFilial | None:
        # BUSCA UN INVENTARIO Y PERMITE BLOQUEARLO DURANTE UNA VENTA.

        consulta = """
            SELECT id_inventario, id_filial, id_producto,
                   stock_disponible, precio_venta_local
            FROM inventarios_filial
            WHERE id_filial = %s AND id_producto = %s
        """
        if bloquear:
            if conexion is None:
                raise ValueError("El bloqueo de stock requiere una transaccion activa.")
            consulta += " FOR UPDATE"

        with self._usar_conexion(conexion) as conexion_actual:
            cursor = conexion_actual.cursor(dictionary=True)
            try:
                cursor.execute(consulta, (id_filial, id_producto))
                fila = cursor.fetchone()
                return self._convertir_fila(fila) if fila else None
            finally:
                cursor.close()

    def crear(
        self,
        inventario: InventarioFilial,
        conexion: MySQLConnectionAbstract | None = None,
    ) -> int:
        # CREA EL STOCK Y PRECIO INICIAL DE UN PRODUCTO EN UNA FILIAL.

        consulta = """
            INSERT INTO inventarios_filial
                (id_filial, id_producto, stock_disponible, precio_venta_local)
            VALUES (%s, %s, %s, %s)
        """
        parametros = (
            inventario.id_filial,
            inventario.id_producto,
            inventario.stock_disponible,
            inventario.precio_venta_local,
        )
        with self._usar_conexion(conexion, escritura=True) as conexion_actual:
            cursor = conexion_actual.cursor()
            try:
                cursor.execute(consulta, parametros)
                inventario.id_inventario = cursor.lastrowid
                return cursor.lastrowid
            finally:
                cursor.close()

    def descontar_stock(
        self,
        id_filial: int,
        id_producto: int,
        cantidad: int,
        conexion: MySQLConnectionAbstract | None = None,
    ) -> None:
        # DESCUENTA UNIDADES SOLAMENTE CUANDO EXISTE SALDO SUFICIENTE.

        # ============================================================
        # BLOQUE: DESCUENTO ATOMICO DE STOCK EN MYSQL
        # La condicion de la consulta evita inventarios negativos incluso
        # si dos ventas intentan descontar el mismo producto.
        # Cumple: RF-03 y CU-03.
        # ============================================================
        unidades = validar_entero_positivo(cantidad, "cantidad a descontar")
        consulta = """
            UPDATE inventarios_filial
            SET stock_disponible = stock_disponible - %s
            WHERE id_filial = %s
              AND id_producto = %s
              AND stock_disponible >= %s
        """
        parametros = (unidades, id_filial, id_producto, unidades)
        with self._usar_conexion(conexion, escritura=True) as conexion_actual:
            cursor = conexion_actual.cursor()
            try:
                cursor.execute(consulta, parametros)
                if cursor.rowcount != 1:
                    raise ValueError("Producto inexistente o stock insuficiente.")
            finally:
                cursor.close()

    def reponer_stock(
        self,
        id_filial: int,
        id_producto: int,
        cantidad: int,
        conexion: MySQLConnectionAbstract | None = None,
    ) -> None:
        # INCREMENTA EL STOCK DURANTE UNA RECEPCION O REVERSION.

        unidades = validar_entero_positivo(cantidad, "cantidad a reponer")
        consulta = """
            UPDATE inventarios_filial
            SET stock_disponible = stock_disponible + %s
            WHERE id_filial = %s AND id_producto = %s
        """
        with self._usar_conexion(conexion, escritura=True) as conexion_actual:
            cursor = conexion_actual.cursor()
            try:
                cursor.execute(consulta, (unidades, id_filial, id_producto))
                if cursor.rowcount != 1:
                    raise ValueError("El producto no existe en la filial.")
            finally:
                cursor.close()

    def actualizar_precio(
        self,
        id_filial: int,
        id_producto: int,
        nuevo_precio: Decimal | str | int,
    ) -> None:
        # ACTUALIZA EL PRECIO LOCAL SIN MODIFICAR EL PRODUCTO CORPORATIVO.

        precio = redondear_moneda(
            validar_decimal_positivo(nuevo_precio, "precio de venta local")
        )
        consulta = """
            UPDATE inventarios_filial
            SET precio_venta_local = %s
            WHERE id_filial = %s AND id_producto = %s
        """
        with self._usar_conexion(escritura=True) as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(consulta, (precio, id_filial, id_producto))
                if cursor.rowcount != 1:
                    raise ValueError("El producto no existe en la filial.")
            finally:
                cursor.close()

