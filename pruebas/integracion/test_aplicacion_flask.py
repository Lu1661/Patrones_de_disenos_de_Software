"""Pruebas de integracion de Flask que no necesitan MySQL."""

from aplicacion.crear_aplicacion import crear_aplicacion


def test_login_protege_el_sistema_y_permite_cerrar_sesion(monkeypatch):
    monkeypatch.setattr(
        "aplicacion.configuracion.configuracion_entorno.ConfiguracionEntorno.MYSQL_USUARIO",
        "",
    )
    monkeypatch.setattr(
        "aplicacion.configuracion.configuracion_entorno.ConfiguracionEntorno.MYSQL_PASSWORD",
        "",
    )
    aplicacion = crear_aplicacion()
    aplicacion.config.update(
        TESTING=True,
        ADMIN_USUARIO="admin",
        ADMIN_PASSWORD="admin",
    )
    cliente = aplicacion.test_client()

    assert cliente.get("/").status_code == 302
    respuesta_sin_sesion = cliente.get("/api/productos")
    assert respuesta_sin_sesion.status_code == 401
    assert respuesta_sin_sesion.get_json()["exito"] is False

    acceso_incorrecto = cliente.post(
        "/login",
        data={"usuario": "admin", "password": "incorrecta"},
    )
    assert acceso_incorrecto.status_code == 401
    assert "Usuario o contraseña incorrectos" in acceso_incorrecto.get_data(
        as_text=True
    )

    acceso_correcto = cliente.post(
        "/login",
        data={"usuario": "admin", "password": "admin"},
    )
    assert acceso_correcto.status_code == 302
    assert cliente.get("/").status_code == 200

    respuesta = cliente.get("/api/productos")
    assert respuesta.status_code == 503
    assert respuesta.get_json()["exito"] is False

    assert cliente.post("/logout").status_code == 302
    assert cliente.get("/").status_code == 302
