"""Punto de entrada local de la aplicacion SERF."""

import os

from aplicacion.crear_aplicacion import crear_aplicacion


aplicacion = crear_aplicacion()


if __name__ == "__main__":
    modo_debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    aplicacion.run(debug=modo_debug)

