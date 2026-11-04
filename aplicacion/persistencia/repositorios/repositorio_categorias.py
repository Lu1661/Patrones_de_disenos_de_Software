# PERSISTENCIA DE LAS CATEGORIAS DE PRODUCTOS.

from aplicacion.dominio.entidades.categoria_producto import CategoriaProducto
from aplicacion.persistencia.conexion.conexion_mysql import ConexionMySQL
from aplicacion.persistencia.repositorios.repositorio_base import RepositorioBase


class RepositorioCategorias(RepositorioBase):
    # GUARDA Y CONSULTA LAS CATEGORIAS DISPONIBLES DEL CATALOGO.

    def __init__(self, administrador_conexion: ConexionMySQL) -> None:
        super().__init__(administrador_conexion)

    @staticmethod
    def _convertir_fila(fila: dict) -> CategoriaProducto:
        return CategoriaProducto(
            nombre=fila["nombre"],
            activa=bool(fila["activa"]),
            id_categoria=fila["id_categoria"],
        )

    def listar(self) -> list[CategoriaProducto]:
        consulta = """
            SELECT id_categoria, nombre, activa
            FROM categorias_productos
            ORDER BY nombre
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta)
                return [self._convertir_fila(fila) for fila in cursor.fetchall()]
            finally:
                cursor.close()

    def obtener_por_nombre(self, nombre: str) -> CategoriaProducto | None:
        consulta = """
            SELECT id_categoria, nombre, activa
            FROM categorias_productos
            WHERE LOWER(nombre) = LOWER(%s)
            LIMIT 1
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta, (nombre,))
                fila = cursor.fetchone()
                return self._convertir_fila(fila) if fila else None
            finally:
                cursor.close()

    def crear(self, categoria: CategoriaProducto) -> int:
        consulta = """
            INSERT INTO categorias_productos (nombre, activa)
            VALUES (%s, %s)
        """
        with self._usar_conexion(escritura=True) as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(consulta, (categoria.nombre, categoria.activa))
                categoria.id_categoria = cursor.lastrowid
                return cursor.lastrowid
            finally:
                cursor.close()
