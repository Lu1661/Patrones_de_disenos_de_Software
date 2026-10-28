# PERSISTENCIA DE VENTAS Y SUS DETALLES.

from datetime import date, datetime, time

from mysql.connector.abstracts import MySQLConnectionAbstract

from aplicacion.dominio.entidades.detalle_venta import DetalleVenta
from aplicacion.dominio.entidades.transaccion_venta import TransaccionVenta
from aplicacion.persistencia.conexion.conexion_mysql import ConexionMySQL
from aplicacion.persistencia.repositorios.repositorio_base import RepositorioBase


class RepositorioVentas(RepositorioBase):
    # GUARDA COMPROBANTES COMPLETOS Y BUSCA SUS DETALLES.

    def __init__(self, administrador_conexion: ConexionMySQL) -> None:
        super().__init__(administrador_conexion)

    def registrar(
        self,
        venta: TransaccionVenta,
        conexion: MySQLConnectionAbstract | None = None,
    ) -> int:
        # GUARDA LA CABECERA Y SUS DETALLES DENTRO DE LA MISMA CONEXION.

        venta.validar_para_registro()
        consulta_venta = """
            INSERT INTO ventas
                (numero_factura, id_filial, fecha_venta, cliente, vendedor,
                 metodo_pago, codigo_divisa, tasa_eur_aplicada,
                 total_local, total_eur)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        consulta_detalle = """
            INSERT INTO detalles_venta
                (id_venta, id_producto, cantidad, precio_unitario_local,
                 subtotal_local, costo_unitario_eur, subtotal_costo_eur)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        with self._usar_conexion(conexion, escritura=True) as conexion_actual:
            cursor = conexion_actual.cursor()
            try:
                cursor.execute(
                    consulta_venta,
                    (
                        venta.numero_factura,
                        venta.id_filial,
                        venta.fecha_venta,
                        venta.cliente,
                        venta.vendedor,
                        venta.metodo_pago,
                        venta.codigo_divisa,
                        venta.tasa_eur_aplicada,
                        venta.total_local,
                        venta.total_eur,
                    ),
                )
                venta.id_venta = cursor.lastrowid

                for detalle in venta.detalles:
                    cursor.execute(
                        consulta_detalle,
                        (
                            venta.id_venta,
                            detalle.id_producto,
                            detalle.cantidad,
                            detalle.precio_unitario_local,
                            detalle.subtotal_local,
                            detalle.costo_unitario_eur,
                            detalle.subtotal_costo_eur,
                        ),
                    )
                    detalle.id_detalle = cursor.lastrowid

                return venta.id_venta
            finally:
                cursor.close()

    def obtener_por_id(self, id_venta: int) -> TransaccionVenta | None:
        # BUSCA UNA VENTA JUNTO CON TODOS SUS PRODUCTOS.

        with self._usar_conexion() as conexion:
            ventas = self._consultar_ventas(
                conexion,
                "WHERE id_venta = %s",
                (id_venta,),
            )
            return ventas[0] if ventas else None

    def listar_por_periodo(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        id_filial: int | None = None,
    ) -> list[TransaccionVenta]:
        # LISTA VENTAS PARA CONSTRUIR REPORTES POR PERIODO Y FILIAL.

        inicio = datetime.combine(fecha_inicio, time.min)
        fin = datetime.combine(fecha_fin, time.max)
        condicion = "WHERE fecha_venta BETWEEN %s AND %s"
        parametros: tuple = (inicio, fin)
        if id_filial is not None:
            condicion += " AND id_filial = %s"
            parametros += (id_filial,)

        with self._usar_conexion() as conexion:
            return self._consultar_ventas(conexion, condicion, parametros)

    def _consultar_ventas(
        self,
        conexion: MySQLConnectionAbstract,
        condicion: str,
        parametros: tuple,
    ) -> list[TransaccionVenta]:
        # CONVIERTE CABECERAS Y DETALLES MYSQL EN ENTIDADES DEL DOMINIO.

        consulta = f"""
            SELECT id_venta, numero_factura, id_filial, fecha_venta,
                   cliente, vendedor, metodo_pago, codigo_divisa,
                   tasa_eur_aplicada
            FROM ventas
            {condicion}
            ORDER BY fecha_venta DESC, id_venta DESC
        """
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(consulta, parametros)
            filas_ventas = cursor.fetchall()
        finally:
            cursor.close()

        ventas: list[TransaccionVenta] = []
        for fila in filas_ventas:
            detalles = self._consultar_detalles(conexion, fila["id_venta"])
            ventas.append(
                TransaccionVenta(
                    numero_factura=fila["numero_factura"],
                    id_filial=fila["id_filial"],
                    fecha_venta=fila["fecha_venta"],
                    cliente=fila["cliente"],
                    vendedor=fila["vendedor"],
                    metodo_pago=fila["metodo_pago"],
                    codigo_divisa=fila["codigo_divisa"],
                    tasa_eur_aplicada=fila["tasa_eur_aplicada"],
                    detalles=detalles,
                    id_venta=fila["id_venta"],
                )
            )
        return ventas

    @staticmethod
    def _consultar_detalles(
        conexion: MySQLConnectionAbstract,
        id_venta: int,
    ) -> list[DetalleVenta]:
        # BUSCA LOS PRODUCTOS ASOCIADOS A UNA VENTA.

        consulta = """
            SELECT id_detalle, id_producto, cantidad,
                   precio_unitario_local, costo_unitario_eur
            FROM detalles_venta
            WHERE id_venta = %s
            ORDER BY id_detalle
        """
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(consulta, (id_venta,))
            return [
                DetalleVenta(
                    id_producto=fila["id_producto"],
                    cantidad=fila["cantidad"],
                    precio_unitario_local=fila["precio_unitario_local"],
                    costo_unitario_eur=fila["costo_unitario_eur"],
                    id_detalle=fila["id_detalle"],
                )
                for fila in cursor.fetchall()
            ]
        finally:
            cursor.close()

