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
    assert aplicacion.config["SECRET_KEY"] not in {
        "clave-local-solo-desarrollo",
        "cambiar_en_el_entorno_local",
    }
    assert aplicacion.config["MAX_CONTENT_LENGTH"] == 1024 * 1024
    cliente = aplicacion.test_client()

    assert cliente.get("/").status_code == 302
    respuesta_sin_sesion = cliente.get("/api/productos")
    assert respuesta_sin_sesion.status_code == 401
    assert respuesta_sin_sesion.get_json()["exito"] is False
    assert respuesta_sin_sesion.headers["X-Content-Type-Options"] == "nosniff"
    assert respuesta_sin_sesion.headers["X-Frame-Options"] == "DENY"
    assert respuesta_sin_sesion.headers["Cache-Control"] == "no-store"
    assert "default-src 'self'" in respuesta_sin_sesion.headers[
        "Content-Security-Policy"
    ]

    acceso_incorrecto = cliente.post(
        "/login",
        data={"usuario": "admin", "password": "incorrecta"},
    )
    assert acceso_incorrecto.status_code == 401
    assert "Usuario o contraseña incorrectos" in acceso_incorrecto.get_data(
        as_text=True
    )

    respuesta_demasiado_grande = cliente.post(
        "/login",
        data={"usuario": "x" * (1024 * 1024 + 1), "password": "x"},
    )
    assert respuesta_demasiado_grande.status_code == 413

    acceso_correcto = cliente.post(
        "/login",
        data={"usuario": "admin", "password": "admin"},
    )
    assert acceso_correcto.status_code == 302
    cookie_sesion = acceso_correcto.headers["Set-Cookie"]
    assert "serf_sesion=" in cookie_sesion
    assert "HttpOnly" in cookie_sesion
    assert "SameSite=Lax" in cookie_sesion
    assert cliente.get("/").status_code == 200

    respuesta = cliente.get("/api/productos")
    assert respuesta.status_code == 503
    assert respuesta.get_json()["exito"] is False

    assert cliente.post("/logout").status_code == 302
    assert cliente.get("/").status_code == 302
