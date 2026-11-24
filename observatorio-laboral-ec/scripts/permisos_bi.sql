-- Permisos de solo lectura para las herramientas de BI (Power BI, Looker Studio).
-- El rol `bi_lector` se crea en la consola de Neon (Roles → New role), que genera su contraseña.
-- Este script solo concede lectura sobre el esquema `marts`: no puede ver `raw` ni modificar nada.

grant usage on schema marts to bi_lector;
grant select on all tables in schema marts to bi_lector;

-- dbt recrea las tablas y vistas en cada ejecución: los permisos por defecto cubren los objetos nuevos.
alter default privileges for role neondb_owner in schema marts grant select on tables to bi_lector;
