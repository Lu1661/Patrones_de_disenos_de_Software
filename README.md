# SERF - Sistema Empresarial de Reportes Financieros

Proyecto académico del curso Patrones de Diseño de Software.

## Tecnologías

- Python 3.10 o superior
- Flask
- MySQL
- HTML, CSS y JavaScript
- pytest

## Estado actual

Las fases 1 a 7 están terminadas. El proyecto cuenta con estructura modular, base de datos MySQL, entidades del dominio, los seis patrones solicitados y repositorios para conservar la información. Los módulos web funcionales se implementarán en las fases siguientes.

## Preparación local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

El archivo `.env` debe completarse localmente y nunca debe enviarse al repositorio.

## Ejecución

```powershell
python ejecutar.py
```

La aplicación quedará disponible en `http://127.0.0.1:5000`.

## Organización

- `aplicacion/dominio`: entidades y contratos del negocio.
- `aplicacion/servicios`: procesos principales del sistema.
- `aplicacion/reportes`: construcción y presentación de reportes.
- `aplicacion/persistencia`: conexión y repositorios MySQL.
- `aplicacion/presentacion`: controladores, plantillas y recursos visuales.
- `base_datos`: scripts SQL ordenados.
- `pruebas`: pruebas unitarias y de integración.

Los patrones solicitados se ubicarán dentro de los módulos donde cumplen una responsabilidad real. No se crearán carpetas separadas por patrón.

