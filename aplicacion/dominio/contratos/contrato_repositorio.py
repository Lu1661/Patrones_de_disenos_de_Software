# CONTRATO PEQUENO PARA REPOSITORIOS CONSULTABLES POR IDENTIFICADOR.

from abc import ABC, abstractmethod
from typing import Generic, TypeVar


Entidad = TypeVar("Entidad")


class IRepositorioConsulta(ABC, Generic[Entidad]):
    # OPERACIONES DE LECTURA COMPARTIDAS SOLAMENTE DONDE CORRESPONDEN.

    @abstractmethod
    def listar(self) -> list[Entidad]:
        # DEVUELVE LOS REGISTROS DISPONIBLES.
        pass

    @abstractmethod
    def obtener_por_id(self, identificador: int) -> Entidad | None:
        # DEVUELVE UNA ENTIDAD O NONE CUANDO NO EXISTE.
        pass

