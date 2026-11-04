# PRUEBAS DE INTEGRACION DE FLASK QUE NO NECESITAN MYSQL.

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
        ADMIN_PASSWORD="clave-admin-prueba",
        SUPERVISOR_USUARIO="supervisor",
        SUPERVISOR_PASSWORD="clave-supervisor-prueba",
        VENDEDOR_USUARIO="vendedor",
        VENDEDOR_PASSWORD="clave-vendedor-prueba",
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
    assert cliente.delete("/api/productos/1").status_code == 401
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
        data={"usuario": "admin", "password": "clave-admin-prueba"},
    )
    assert acceso_correcto.status_code == 302
    cookie_sesion = acceso_correcto.headers["Set-Cookie"]
    assert "serf_sesion=" in cookie_sesion
    assert "HttpOnly" in cookie_sesion
    assert "SameSite=Lax" in cookie_sesion
    assert cliente.get("/").status_code == 302
    assert cliente.get("/resumen").status_code == 200

    respuesta = cliente.get("/api/productos")
    assert respuesta.status_code == 503
    assert respuesta.get_json()["exito"] is False

    assert cliente.post("/logout").status_code == 302
    assert cliente.get("/").status_code == 302
    assert cliente.put("/api/configuracion/filiales/1", json={}).status_code == 401


def test_roles_limitan_menus_rutas_y_operaciones(monkeypatch):
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
        ADMIN_PASSWORD="clave-admin-prueba",
        SUPERVISOR_USUARIO="supervisor",
        SUPERVISOR_PASSWORD="clave-supervisor-prueba",
        VENDEDOR_USUARIO="vendedor",
        VENDEDOR_PASSWORD="clave-vendedor-prueba",
    )

    administrador = aplicacion.test_client()
    assert administrador.post(
        "/login",
        data={"usuario": "admin", "password": "clave-admin-prueba"},
    ).status_code == 302
    pagina_admin = administrador.get("/configuracion")
    assert pagina_admin.status_code == 200
    assert "Rol: <strong>Administrador</strong>" in pagina_admin.get_data(as_text=True)

    supervisor = aplicacion.test_client()
    assert supervisor.post(
        "/login",
        data={
            "usuario": "supervisor",
            "password": "clave-supervisor-prueba",
        },
    ).status_code == 302
    pagina_supervisor = supervisor.get("/resumen")
    html_supervisor = pagina_supervisor.get_data(as_text=True)
    assert pagina_supervisor.status_code == 200
    assert "Rol: <strong>Supervisor</strong>" in html_supervisor
    assert 'title="Configuración"' not in html_supervisor
    assert 'title="Inventario"' in html_supervisor
    assert supervisor.get("/configuracion").status_code == 403
    assert supervisor.post("/api/configuracion/filiales", json={}).status_code == 403
    assert supervisor.delete("/api/productos/1").status_code == 403

    vendedor = aplicacion.test_client()
    assert vendedor.post(
        "/login",
        data={"usuario": "vendedor", "password": "clave-vendedor-prueba"},
    ).status_code == 302
    pagina_vendedor = vendedor.get("/resumen")
    html_vendedor = pagina_vendedor.get_data(as_text=True)
    assert pagina_vendedor.status_code == 200
    assert "Rol: <strong>Vendedor</strong>" in html_vendedor
    assert 'title="Configuración"' not in html_vendedor
    assert 'title="Inventario"' not in html_vendedor
    assert 'title="Reportes"' not in html_vendedor
    assert 'title="Productos"' in html_vendedor
    assert 'title="Ventas"' in html_vendedor
    assert vendedor.get("/productos").status_code == 200
    assert vendedor.get("/ventas").status_code == 200
    assert vendedor.get("/inventario").status_code == 403
    assert vendedor.get("/reportes").status_code == 403
    assert vendedor.get("/api/inventario?id_filial=1").status_code == 403
    assert vendedor.post("/api/reportes/generar", json={}).status_code == 403
