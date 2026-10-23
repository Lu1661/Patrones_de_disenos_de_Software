"""Contrato pequeno para repositorios consultables por identificador."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar


Entidad = TypeVar("Entidad")


class IRepositorioConsulta(ABC, Generic[Entidad]):
    """Operaciones de lectura compartidas solamente donde corresponden."""

    @abstractmethod
    def listar(self) -> list[Entidad]:
        """Retorna los registros disponibles."""

    @abstractmethod
    def obtener_por_id(self, identificador: int) -> Entidad | None:
        """Retorna una entidad o None cuando no existe."""

