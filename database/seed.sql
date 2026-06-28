-- ============================================================
-- MYTHOS — Seed / Bootstrap de empresa y roles
-- Ejecutar en: Supabase Dashboard → SQL Editor → New Query
-- ============================================================
-- Resuelve el arranque desde cero: crea una empresa y permite
-- promover usuarios a admin/supervisor (la UI sólo registra
-- empleados, así que el primer admin se crea acá).
--
-- FLUJO RECOMENDADO:
--   1. Ejecutá el PASO 1 → copiá el company_id que devuelve.
--   2. En la app (pantalla Registrarse) creá las cuentas usando
--      ese company_id. Todas quedan como 'employee'.
--   3. Ejecutá el PASO 2 para promover admin y supervisor.
--   4. Los promovidos deben cerrar sesión y volver a entrar para
--      que su JWT tome el nuevo rol.
-- ============================================================


-- ─────────────────────────────────────────────────────────────
-- PASO 1 — Crear la empresa demo (idempotente) y ver su ID
-- ─────────────────────────────────────────────────────────────
insert into companies (name)
select 'Empresa Demo'
where not exists (select 1 from companies where name = 'Empresa Demo');

select id as company_id, name
from companies
where name = 'Empresa Demo';
-- 👆 Copiá el company_id: lo usan los empleados para registrarse.


-- ─────────────────────────────────────────────────────────────
-- PASO 2 — Promover un usuario ya registrado a admin/supervisor
-- ─────────────────────────────────────────────────────────────
-- Reemplazá el email por el del usuario y ejecutá el bloque que
-- corresponda. Actualiza profiles (para el dashboard) y
-- raw_user_meta_data (para que el JWT lo refleje al re-loguear).

-- ► Promover a ADMIN ──────────────────────────────────────────
update profiles set role = 'admin'
where id = (select id from auth.users where email = 'admin@tuempresa.com');

update auth.users
set raw_user_meta_data = jsonb_set(coalesce(raw_user_meta_data, '{}'::jsonb), '{role}', '"admin"')
where email = 'admin@tuempresa.com';

-- ► Promover a SUPERVISOR ─────────────────────────────────────
update profiles set role = 'supervisor'
where id = (select id from auth.users where email = 'supervisor@tuempresa.com');

update auth.users
set raw_user_meta_data = jsonb_set(coalesce(raw_user_meta_data, '{}'::jsonb), '{role}', '"supervisor"')
where email = 'supervisor@tuempresa.com';


-- ─────────────────────────────────────────────────────────────
-- PASO 3 (opcional) — Asignar empresa a un usuario sin empresa
-- ─────────────────────────────────────────────────────────────
-- Útil si alguien se registró sin company_id. Reemplazá el email
-- y el <COMPANY_ID> por el del PASO 1.

-- update profiles set company_id = '<COMPANY_ID>'
-- where id = (select id from auth.users where email = 'usuario@tuempresa.com');

-- update auth.users
-- set raw_user_meta_data = jsonb_set(coalesce(raw_user_meta_data, '{}'::jsonb), '{company_id}', to_jsonb('<COMPANY_ID>'::text))
-- where email = 'usuario@tuempresa.com';


-- ─────────────────────────────────────────────────────────────
-- VERIFICACIÓN — quién es quién
-- ─────────────────────────────────────────────────────────────
select p.full_name, u.email, p.role, p.company_id
from profiles p
join auth.users u on u.id = p.id
order by p.role, p.full_name;
