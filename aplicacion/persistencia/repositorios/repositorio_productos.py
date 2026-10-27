"""Persistencia de productos importados."""

from mysql.connector.abstracts import MySQLConnectionAbstract

from aplicacion.dominio.contratos.contrato_repositorio import IRepositorioConsulta
from aplicacion.dominio.entidades.producto_importado import ProductoImportado
from aplicacion.persistencia.conexion.conexion_mysql import ConexionMySQL
from aplicacion.persistencia.repositorios.repositorio_base import RepositorioBase


class RepositorioProductos(
    RepositorioBase,
    IRepositorioConsulta[ProductoImportado],
):
    """Guarda y consulta el catalogo corporativo de productos."""

    def __init__(self, administrador_conexion: ConexionMySQL) -> None:
        super().__init__(administrador_conexion)

    @staticmethod
    def _convertir_fila(fila: dict) -> ProductoImportado:
        return ProductoImportado(
            codigo=fila["codigo"],
            nombre=fila["nombre"],
            descripcion_tecnica=fila["descripcion_tecnica"],
            categoria=fila["categoria"],
            costo_unitario_cny=fila["costo_unitario_cny"],
            costo_unitario_eur=fila["costo_unitario_eur"],
            proveedor=fila["proveedor"],
            fecha_importacion=fila["fecha_importacion"],
            activo=bool(fila["activo"]),
            id_producto=fila["id_producto"],
        )

    def listar(self) -> list[ProductoImportado]:
        """Lista el catalogo ordenado por nombre."""

        consulta = """
            SELECT id_producto, codigo, nombre, descripcion_tecnica,
                   categoria, costo_unitario_cny, costo_unitario_eur,
                   proveedor, fecha_importacion, activo
            FROM productos_importados
            ORDER BY nombre
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta)
                return [self._convertir_fila(fila) for fila in cursor.fetchall()]
            finally:
                cursor.close()

    def obtener_por_id(self, identificador: int) -> ProductoImportado | None:
        """Busca un producto por su clave primaria."""

        return self._obtener_por("id_producto", identificador)

    def obtener_por_codigo(self, codigo: str) -> ProductoImportado | None:
        """Busca un producto por su codigo corporativo."""

        return self._obtener_por("codigo", codigo.strip().upper())

    def _obtener_por(self, columna: str, valor: object) -> ProductoImportado | None:
        """Ejecuta las dos busquedas permitidas sin aceptar columnas externas."""

        if columna not in {"id_producto", "codigo"}:
            raise ValueError("La columna de busqueda no es valida.")
        consulta = f"""
            SELECT id_producto, codigo, nombre, descripcion_tecnica,
                   categoria, costo_unitario_cny, costo_unitario_eur,
                   proveedor, fecha_importacion, activo
            FROM productos_importados
            WHERE {columna} = %s
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta, (valor,))
                fila = cursor.fetchone()
                return self._convertir_fila(fila) if fila else None
            finally:
                cursor.close()

    def crear(
        self,
        producto: ProductoImportado,
        conexion: MySQLConnectionAbstract | None = None,
    ) -> int:
        """Inserta un producto y retorna su identificador."""

        consulta = """
            INSERT INTO productos_importados
                (codigo, nombre, descripcion_tecnica, categoria,
                 costo_unitario_cny, costo_unitario_eur,
                 proveedor, fecha_importacion, activo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        parametros = (
            producto.codigo,
            producto.nombre,
            producto.descripcion_tecnica,
            producto.categoria,
            producto.costo_unitario_cny,
            producto.costo_unitario_eur,
            producto.proveedor,
            producto.fecha_importacion,
            producto.activo,
        )
        with self._usar_conexion(conexion, escritura=True) as conexion_actual:
            cursor = conexion_actual.cursor()
            try:
                cursor.execute(consulta, parametros)
                producto.id_producto = cursor.lastrowid
                return cursor.lastrowid
            finally:
                cursor.close()

    def actualizar(self, producto: ProductoImportado) -> None:
        """Actualiza los datos tecnicos y costos de un producto."""

        consulta = """
            UPDATE productos_importados
            SET codigo = %s, nombre = %s, descripcion_tecnica = %s,
                categoria = %s, costo_unitario_cny = %s,
                costo_unitario_eur = %s, proveedor = %s,
                fecha_importacion = %s
            WHERE id_producto = %s
        """
        parametros = (
            producto.codigo,
            producto.nombre,
            producto.descripcion_tecnica,
            producto.categoria,
            producto.costo_unitario_cny,
            producto.costo_unitario_eur,
            producto.proveedor,
            producto.fecha_importacion,
            producto.id_producto,
        )
        with self._usar_conexion(escritura=True) as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(consulta, parametros)
            finally:
                cursor.close()

    def desactivar(self, id_producto: int) -> None:
        """Marca un producto como inactivo y conserva sus movimientos."""

        with self._usar_conexion(escritura=True) as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(
                    "UPDATE productos_importados SET activo = FALSE "
                    "WHERE id_producto = %s AND activo = TRUE",
                    (id_producto,),
                )
                if cursor.rowcount == 0:
                    raise ValueError("El producto indicado no existe o ya esta inactivo.")
            finally:
                cursor.close()

