"""Persistencia de filiales."""

from mysql.connector.abstracts import MySQLConnectionAbstract

from aplicacion.dominio.contratos.contrato_repositorio import IRepositorioConsulta
from aplicacion.dominio.entidades.filial import Filial
from aplicacion.persistencia.conexion.conexion_mysql import ConexionMySQL
from aplicacion.persistencia.repositorios.repositorio_base import RepositorioBase


class RepositorioFiliales(RepositorioBase, IRepositorioConsulta[Filial]):
    """Guarda y consulta las sedes comerciales de FinanCorp."""

    def __init__(self, administrador_conexion: ConexionMySQL) -> None:
        super().__init__(administrador_conexion)

    @staticmethod
    def _convertir_fila(fila: dict) -> Filial:
        return Filial(
            codigo=fila["codigo"],
            nombre=fila["nombre"],
            pais=fila["pais"],
            ciudad=fila["ciudad"],
            codigo_divisa=fila["codigo_divisa"],
            activa=bool(fila["activa"]),
            id_filial=fila["id_filial"],
        )

    def listar(self) -> list[Filial]:
        """Lista todas las filiales ordenadas por nombre."""

        consulta = """
            SELECT id_filial, codigo, nombre, pais, ciudad,
                   codigo_divisa, activa
            FROM filiales
            ORDER BY nombre
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta)
                return [self._convertir_fila(fila) for fila in cursor.fetchall()]
            finally:
                cursor.close()

    def listar_activas(self) -> list[Filial]:
        """Lista las filiales habilitadas para registrar operaciones."""

        return [filial for filial in self.listar() if filial.activa]

    def obtener_por_id(self, identificador: int) -> Filial | None:
        """Busca una filial por su clave primaria."""

        consulta = """
            SELECT id_filial, codigo, nombre, pais, ciudad,
                   codigo_divisa, activa
            FROM filiales
            WHERE id_filial = %s
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta, (identificador,))
                fila = cursor.fetchone()
                return self._convertir_fila(fila) if fila else None
            finally:
                cursor.close()

    def crear(
        self,
        filial: Filial,
        conexion: MySQLConnectionAbstract | None = None,
    ) -> int:
        """Inserta una filial y retorna su identificador."""

        consulta = """
            INSERT INTO filiales
                (codigo, nombre, pais, ciudad, codigo_divisa, activa)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        parametros = (
            filial.codigo,
            filial.nombre,
            filial.pais,
            filial.ciudad,
            filial.codigo_divisa,
            filial.activa,
        )
        with self._usar_conexion(conexion, escritura=True) as conexion_actual:
            cursor = conexion_actual.cursor()
            try:
                cursor.execute(consulta, parametros)
                filial.id_filial = cursor.lastrowid
                return cursor.lastrowid
            finally:
                cursor.close()

    def actualizar(self, filial: Filial) -> None:
        """Actualiza los datos administrativos de una filial existente."""

        consulta = """
            UPDATE filiales
            SET codigo = %s, nombre = %s, pais = %s, ciudad = %s,
                codigo_divisa = %s
            WHERE id_filial = %s
        """
        parametros = (
            filial.codigo,
            filial.nombre,
            filial.pais,
            filial.ciudad,
            filial.codigo_divisa,
            filial.id_filial,
        )
        with self._usar_conexion(escritura=True) as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(consulta, parametros)
            finally:
                cursor.close()

    def desactivar(self, id_filial: int) -> None:
        """Marca una filial como inactiva sin borrar su historial."""

        with self._usar_conexion(escritura=True) as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(
                    "UPDATE filiales SET activa = FALSE "
                    "WHERE id_filial = %s AND activa = TRUE",
                    (id_filial,),
                )
                if cursor.rowcount == 0:
                    raise ValueError("La filial indicada no existe o ya esta inactiva.")
            finally:
                cursor.close()

