"""Persistencia de tipos de cambio."""

from datetime import date

from mysql.connector.abstracts import MySQLConnectionAbstract

from aplicacion.dominio.entidades.tipo_cambio import TipoCambio
from aplicacion.dominio.validaciones import normalizar_codigo_iso
from aplicacion.persistencia.conexion.conexion_mysql import ConexionMySQL
from aplicacion.persistencia.repositorios.repositorio_base import RepositorioBase


class RepositorioTiposCambio(RepositorioBase):
    """Mantiene el historial de tasas utilizadas para convertir a EUR."""

    def __init__(self, administrador_conexion: ConexionMySQL) -> None:
        super().__init__(administrador_conexion)

    @staticmethod
    def _convertir_fila(fila: dict) -> TipoCambio:
        return TipoCambio(
            codigo_divisa_origen=fila["codigo_divisa_origen"],
            codigo_divisa_destino=fila["codigo_divisa_destino"],
            tasa=fila["tasa"],
            fecha_vigencia=fila["fecha_vigencia"],
            activa=bool(fila["activa"]),
            id_tipo_cambio=fila["id_tipo_cambio"],
        )

    def listar(self) -> list[TipoCambio]:
        """Lista las tasas desde la vigencia mas reciente."""

        consulta = """
            SELECT id_tipo_cambio, codigo_divisa_origen,
                   codigo_divisa_destino, tasa, fecha_vigencia, activa
            FROM tipos_cambio
            ORDER BY fecha_vigencia DESC, codigo_divisa_origen
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta)
                return [self._convertir_fila(fila) for fila in cursor.fetchall()]
            finally:
                cursor.close()

    def obtener_vigente(
        self,
        codigo_divisa_origen: str,
        fecha_referencia: date | None = None,
    ) -> TipoCambio | None:
        """Obtiene la ultima tasa activa aplicable a una fecha."""

        codigo = normalizar_codigo_iso(codigo_divisa_origen)
        fecha_busqueda = fecha_referencia or date.today()
        consulta = """
            SELECT id_tipo_cambio, codigo_divisa_origen,
                   codigo_divisa_destino, tasa, fecha_vigencia, activa
            FROM tipos_cambio
            WHERE codigo_divisa_origen = %s
              AND codigo_divisa_destino = 'EUR'
              AND activa = TRUE
              AND fecha_vigencia <= %s
            ORDER BY fecha_vigencia DESC
            LIMIT 1
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta, (codigo, fecha_busqueda))
                fila = cursor.fetchone()
                return self._convertir_fila(fila) if fila else None
            finally:
                cursor.close()

    def obtener_por_id(self, id_tipo_cambio: int) -> TipoCambio | None:
        """Busca una tasa por su identificador administrativo."""

        consulta = """
            SELECT id_tipo_cambio, codigo_divisa_origen,
                   codigo_divisa_destino, tasa, fecha_vigencia, activa
            FROM tipos_cambio
            WHERE id_tipo_cambio = %s
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta, (id_tipo_cambio,))
                fila = cursor.fetchone()
                return self._convertir_fila(fila) if fila else None
            finally:
                cursor.close()

    def registrar(
        self,
        tipo_cambio: TipoCambio,
        conexion: MySQLConnectionAbstract | None = None,
    ) -> int:
        """Desactiva la tasa anterior y registra la nueva en una operacion."""

        with self._usar_conexion(conexion, escritura=True) as conexion_actual:
            cursor = conexion_actual.cursor()
            try:
                if tipo_cambio.activa:
                    cursor.execute(
                        """
                        UPDATE tipos_cambio
                        SET activa = FALSE
                        WHERE codigo_divisa_origen = %s
                          AND codigo_divisa_destino = 'EUR'
                          AND activa = TRUE
                        """,
                        (tipo_cambio.codigo_divisa_origen,),
                    )

                cursor.execute(
                    """
                    INSERT INTO tipos_cambio
                        (codigo_divisa_origen, codigo_divisa_destino,
                         tasa, fecha_vigencia, activa)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        tipo_cambio.codigo_divisa_origen,
                        tipo_cambio.codigo_divisa_destino,
                        tipo_cambio.tasa,
                        tipo_cambio.fecha_vigencia,
                        tipo_cambio.activa,
                    ),
                )
                tipo_cambio.id_tipo_cambio = cursor.lastrowid
                return cursor.lastrowid
            finally:
                cursor.close()

    def actualizar(self, tipo_cambio: TipoCambio) -> None:
        """Actualiza una tasa y conserva una sola tasa activa por divisa."""

        with self._usar_conexion(escritura=True) as conexion:
            cursor = conexion.cursor()
            try:
                if tipo_cambio.activa:
                    cursor.execute(
                        """
                        UPDATE tipos_cambio
                        SET activa = FALSE
                        WHERE codigo_divisa_origen = %s
                          AND codigo_divisa_destino = 'EUR'
                          AND id_tipo_cambio <> %s
                          AND activa = TRUE
                        """,
                        (
                            tipo_cambio.codigo_divisa_origen,
                            tipo_cambio.id_tipo_cambio,
                        ),
                    )
                cursor.execute(
                    """
                    UPDATE tipos_cambio
                    SET codigo_divisa_origen = %s, tasa = %s,
                        fecha_vigencia = %s
                    WHERE id_tipo_cambio = %s
                    """,
                    (
                        tipo_cambio.codigo_divisa_origen,
                        tipo_cambio.tasa,
                        tipo_cambio.fecha_vigencia,
                        tipo_cambio.id_tipo_cambio,
                    ),
                )
            finally:
                cursor.close()

    def desactivar(self, id_tipo_cambio: int) -> None:
        """Marca una tasa como historica sin eliminarla fisicamente."""

        with self._usar_conexion(escritura=True) as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(
                    "UPDATE tipos_cambio SET activa = FALSE "
                    "WHERE id_tipo_cambio = %s AND activa = TRUE",
                    (id_tipo_cambio,),
                )
                if cursor.rowcount == 0:
                    raise ValueError("La tasa indicada no existe o ya esta inactiva.")
            finally:
                cursor.close()

