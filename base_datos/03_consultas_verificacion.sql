-- ============================================================
-- PROYECTO: SERF
-- ARCHIVO: CONSULTAS DE VERIFICACION
-- Estas consultas son de solo lectura y permiten revisar que la
-- estructura y los datos iniciales fueron creados correctamente.
-- ============================================================

USE financorp_db;

SELECT
    TABLE_NAME AS tabla,
    ENGINE AS motor,
    TABLE_COLLATION AS cotejamiento
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
ORDER BY TABLE_NAME;

SELECT
    TABLE_NAME AS tabla,
    COLUMN_NAME AS columna,
    COLUMN_TYPE AS tipo,
    IS_NULLABLE AS permite_nulo,
    COLUMN_KEY AS tipo_clave
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
ORDER BY TABLE_NAME, ORDINAL_POSITION;

SELECT
    TABLE_NAME AS tabla,
    CONSTRAINT_NAME AS restriccion,
    CONSTRAINT_TYPE AS tipo
FROM information_schema.TABLE_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = DATABASE()
ORDER BY TABLE_NAME, CONSTRAINT_TYPE, CONSTRAINT_NAME;

SELECT codigo_iso, nombre, simbolo, activa
FROM divisas
ORDER BY codigo_iso;

SELECT
    codigo_divisa_origen,
    codigo_divisa_destino,
    tasa,
    fecha_vigencia,
    activa
FROM tipos_cambio
ORDER BY codigo_divisa_origen, fecha_vigencia DESC;

