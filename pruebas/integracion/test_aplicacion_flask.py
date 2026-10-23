"""Pruebas de integracion de Flask que no necesitan MySQL."""

from aplicacion.crear_aplicacion import crear_aplicacion


def test_inicio_funciona_y_api_informa_si_faltan_credenciales(monkeypatch):
    monkeypatch.setattr(
        "aplicacion.configuracion.configuracion_entorno.ConfiguracionEntorno.MYSQL_USUARIO",
        "",
    )
    monkeypatch.setattr(
        "aplicacion.configuracion.configuracion_entorno.ConfiguracionEntorno.MYSQL_PASSWORD",
        "",
    )
    aplicacion = crear_aplicacion()
    cliente = aplicacion.test_client()

    assert cliente.get("/").status_code == 200
    respuesta = cliente.get("/api/productos")
    assert respuesta.status_code == 503
    assert respuesta.get_json()["exito"] is False
