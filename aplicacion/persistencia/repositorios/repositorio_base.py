"""Apoyo comun para abrir conexiones dentro de los repositorios."""

from contextlib import contextmanager
from typing import Iterator

from mysql.connector.abstracts import MySQLConnectionAbstract

from aplicacion.persistencia.conexion.conexion_mysql import ConexionMySQL


class RepositorioBase:
    """Evita repetir la apertura, confirmacion y cierre de conexiones."""

    def __init__(self, administrador_conexion: ConexionMySQL) -> None:
        self._administrador_conexion = administrador_conexion

    @contextmanager
    def _usar_conexion(
        self,
        conexion_externa: MySQLConnectionAbstract | None = None,
        *,
        escritura: bool = False,
    ) -> Iterator[MySQLConnectionAbstract]:
        """Usa una conexion compartida o administra una conexion propia."""

        conexion_propia = conexion_externa is None
        conexion = conexion_externa or self._administrador_conexion.abrir()

        try:
            yield conexion
            if conexion_propia and escritura:
                conexion.commit()
        except Exception:
            if conexion_propia and escritura:
                conexion.rollback()
            raise
        finally:
            if conexion_propia:
                conexion.close()
