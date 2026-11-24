-- Permisos de solo lectura para las herramientas de BI (Power BI, Looker Studio).
-- IMPORTANTE: el rol se crea con SQL (SQL Editor de Neon), NO desde la consola. Neon hace miembros de
-- `neon_superuser` a los roles creados en la consola (pueden leer y escribir todo, crear bases y roles) y el dueño
-- de la base no puede quitárselo. Un rol creado con SQL nace sin privilegios:
--     CREATE ROLE bi_lector WITH LOGIN PASSWORD '<contraseña elegida por el dueño>';
-- Este script solo concede lectura sobre el esquema `marts`: no puede ver `raw` ni modificar nada.

grant usage on schema marts to bi_lector;
grant select on all tables in schema marts to bi_lector;

-- dbt recrea las tablas y vistas en cada ejecución: los permisos por defecto cubren los objetos nuevos.
alter default privileges for role neondb_owner in schema marts grant select on tables to bi_lector;
