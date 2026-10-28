# APOYO COMUN PARA ABRIR CONEXIONES DENTRO DE LOS REPOSITORIOS.

from contextlib import contextmanager
from typing import Iterator

from mysql.connector.abstracts import MySQLConnectionAbstract

from aplicacion.persistencia.conexion.conexion_mysql import ConexionMySQL


class RepositorioBase:
    # EVITA REPETIR LA APERTURA, CONFIRMACION Y CIERRE DE CONEXIONES.

    def __init__(self, administrador_conexion: ConexionMySQL) -> None:
        self._administrador_conexion = administrador_conexion

    @contextmanager
    def _usar_conexion(
        self,
        conexion_externa: MySQLConnectionAbstract | None = None,
        *,
        escritura: bool = False,
    ) -> Iterator[MySQLConnectionAbstract]:
        # USA UNA CONEXION COMPARTIDA O ADMINISTRA UNA CONEXION PROPIA.

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
