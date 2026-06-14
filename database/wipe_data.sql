-- ============================================================
-- MYTHOS — Vaciado de datos transaccionales
-- ============================================================
-- Borra TODOS los datos del flujo del MVP (documentos, módulos,
-- chats, cuestionarios, diagnósticos, progreso) pero PRESERVA:
--   - Usuarios (auth.users, auth.identities)
--   - Perfiles (profiles)
--   - Empresas (companies)
--
-- Ejecutar en: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

BEGIN;

-- 1. Análisis de brechas de Artemis
DELETE FROM breach_analyses;

-- 2. Resultados de quiz (calificaciones de Artemis)
DELETE FROM quiz_results;

-- 3. Preguntas de quiz generadas por Artemis
DELETE FROM quiz_questions;

-- 4. Historial de chat (mensajes empleado ↔ Apollo/Atlas)
DELETE FROM chat_messages;

-- 5. Progreso del empleado (tiempo dedicado, estado de módulos)
DELETE FROM employee_progress;

-- 6. Módulos de onboarding (ruta generada por Atlas)
DELETE FROM modules;

-- 7. Fragmentos vectoriales (chunks indexados en pgvector)
DELETE FROM document_chunks;

-- 8. Documentos corporativos cargados
DELETE FROM documents;

COMMIT;

-- ============================================================
-- VERIFICACIÓN
-- ============================================================
SELECT
  (SELECT COUNT(*) FROM documents)         AS docs,
  (SELECT COUNT(*) FROM document_chunks)   AS chunks,
  (SELECT COUNT(*) FROM modules)           AS modulos,
  (SELECT COUNT(*) FROM employee_progress) AS progreso,
  (SELECT COUNT(*) FROM chat_messages)     AS chats,
  (SELECT COUNT(*) FROM quiz_questions)    AS preguntas,
  (SELECT COUNT(*) FROM quiz_results)      AS resultados,
  (SELECT COUNT(*) FROM breach_analyses)   AS diagnosticos,
  (SELECT COUNT(*) FROM profiles)          AS usuarios_intactos,
  (SELECT COUNT(*) FROM companies)         AS empresas_intactas;

-- Todos los conteos transaccionales deben dar 0.
-- usuarios_intactos y empresas_intactas deben mantener su valor previo.
