-- ============================================================
-- PROYECTO: SERF
-- ARCHIVO: DATOS INICIALES ESTABLES
-- Este archivo no contiene tasas comerciales variables ni datos
-- inventados de filiales, productos, inventarios o ventas.
-- ============================================================

USE financorp_db;

SET NAMES utf8mb4;

-- ============================================================
-- BLOQUE: DIVISAS RECONOCIDAS
-- Se registran las monedas mencionadas en la documentacion.
-- INSERT IGNORE permite volver a ejecutar el script sin duplicarlas.
-- ============================================================
INSERT IGNORE INTO divisas (codigo_iso, nombre, simbolo, activa)
VALUES
    ('EUR', 'Euro', '€', TRUE),
    ('CNY', 'Yuan chino', '¥', TRUE),
    ('PEN', 'Sol peruano', 'S/', TRUE),
    ('USD', 'Dolar estadounidense', '$', TRUE);

-- ============================================================
-- BLOQUE: EQUIVALENCIA FIJA DE LA MONEDA CORPORATIVA
-- Un importe expresado en EUR se mantiene sin conversion.
-- Las demas tasas se registraran desde el modulo de configuracion.
-- ============================================================
INSERT INTO tipos_cambio (
    codigo_divisa_origen,
    codigo_divisa_destino,
    tasa,
    fecha_vigencia,
    activa
)
SELECT 'EUR', 'EUR', 1.00000000, '2000-01-01', TRUE
WHERE NOT EXISTS (
    SELECT 1
    FROM tipos_cambio
    WHERE codigo_divisa_origen = 'EUR'
      AND codigo_divisa_destino = 'EUR'
      AND activa = TRUE
);

