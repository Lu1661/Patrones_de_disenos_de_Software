# CREACION, CONFIRMACION Y CIERRE DE CONEXIONES MYSQL.

import os
from contextlib import contextmanager
from typing import Iterator

import mysql.connector
from dotenv import load_dotenv
from mysql.connector.abstracts import MySQLConnectionAbstract


class ConexionMySQL:
    # CENTRALIZA LOS DATOS TECNICOS NECESARIOS PARA CONECTARSE A MYSQL.

    def __init__(
        self,
        host: str,
        puerto: int,
        base_datos: str,
        usuario: str,
        password: str,
    ) -> None:
        self._host = host
        self._puerto = puerto
        self._base_datos = base_datos
        self._usuario = usuario
        self._password = password
        self._validar_configuracion()

    @classmethod
    def desde_entorno(cls) -> "ConexionMySQL":
        # CONSTRUYE LA CONEXION SIN INCLUIR CREDENCIALES DENTRO DEL CODIGO.

        load_dotenv()
        return cls(
            host=os.getenv("MYSQL_HOST", "localhost"),
            puerto=int(os.getenv("MYSQL_PORT", "3306")),
            base_datos=os.getenv("MYSQL_BASE_DATOS", ""),
            usuario=os.getenv("MYSQL_USUARIO", ""),
            password=os.getenv("MYSQL_PASSWORD", ""),
        )

    def _validar_configuracion(self) -> None:
        # INFORMA CLARAMENTE CUANDO FALTA UN DATO LOCAL DE CONEXION.

        if not self._host.strip():
            raise ValueError("Falta MYSQL_HOST en la configuracion.")
        if not isinstance(self._puerto, int) or self._puerto <= 0:
            raise ValueError("MYSQL_PORT debe ser un entero mayor que cero.")
        if not self._base_datos.strip():
            raise ValueError("Falta MYSQL_BASE_DATOS en la configuracion.")
        if not self._usuario.strip():
            raise ValueError("Falta MYSQL_USUARIO en la configuracion.")
        if not self._password:
            raise ValueError("Falta MYSQL_PASSWORD en la configuracion.")

    def abrir(self) -> MySQLConnectionAbstract:
        # ABRE UNA CONEXION NUEVA QUE EL PROCESO LLAMADOR DEBE CERRAR.

        # ============================================================
        # BLOQUE: APERTURA SEGURA DE LA CONEXION MYSQL
        # Este bloque usa exclusivamente variables del entorno y nunca
        # escribe la contraseña dentro de consultas o archivos del codigo.
        # ============================================================
        return mysql.connector.connect(
            host=self._host,
            port=self._puerto,
            database=self._base_datos,
            user=self._usuario,
            password=self._password,
            charset="utf8mb4",
            use_unicode=True,
            autocommit=False,
        )

    @contextmanager
    def transaccion(self) -> Iterator[MySQLConnectionAbstract]:
        # CONFIRMA EL CONJUNTO COMPLETO O REVIERTE TODO ANTE UN ERROR.

        conexion = self.abrir()
        try:
            conexion.start_transaction()
            yield conexion
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def probar_conexion(self) -> bool:
        # EJECUTA UNA CONSULTA MINIMA SIN MODIFICAR INFORMACION.

        conexion = self.abrir()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)
        finally:
            cursor.close()
            conexion.close()

