-- ============================================================
-- Mythos — Schema Supabase
-- Ejecutar en: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

create extension if not exists vector;

-- ============================================================
-- EMPRESAS (multi-tenant)
-- ============================================================
create table if not exists companies (
  id         uuid default gen_random_uuid() primary key,
  name       text not null,
  created_at timestamptz default now()
);

-- ============================================================
-- PERFILES (extiende auth.users de Supabase)
-- ============================================================
create table if not exists profiles (
  id         uuid references auth.users primary key,
  company_id uuid references companies(id),
  role       text check (role in ('admin', 'supervisor', 'employee')) not null,
  full_name  text not null,
  created_at timestamptz default now()
);

-- Trigger: crear perfil automáticamente al registrar usuario
create or replace function handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into profiles (id, full_name, role, company_id)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name', new.email),
    coalesce(new.raw_user_meta_data->>'role', 'employee'),
    (new.raw_user_meta_data->>'company_id')::uuid
  );
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure handle_new_user();

-- ============================================================
-- DOCUMENTOS
-- ============================================================
create table if not exists documents (
  id           uuid default gen_random_uuid() primary key,
  company_id   uuid references companies(id),
  filename     text not null,
  storage_path text not null,
  processed    boolean default false,
  created_at   timestamptz default now()
);

-- ============================================================
-- CHUNKS — Atlas los usa para RAG
-- ============================================================
create table if not exists document_chunks (
  id          uuid default gen_random_uuid() primary key,
  document_id uuid references documents(id) on delete cascade,
  company_id  uuid references companies(id),
  content     text not null,
  embedding   vector(768),
  chunk_index integer,
  created_at  timestamptz default now()
);

create index if not exists idx_chunks_embedding
  on document_chunks using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- Función de búsqueda semántica que usa Atlas
create or replace function match_documents(
  query_embedding  vector(768),
  match_company_id uuid,
  match_threshold  float default 0.65,
  match_count      int   default 5
)
returns table(id uuid, content text, similarity float)
language sql stable as $$
  select
    dc.id,
    dc.content,
    1 - (dc.embedding <=> query_embedding) as similarity
  from document_chunks dc
  where dc.company_id = match_company_id
    and 1 - (dc.embedding <=> query_embedding) > match_threshold
  order by dc.embedding <=> query_embedding
  limit match_count;
$$;

-- ============================================================
-- MÓDULOS DE ONBOARDING (generados por Atlas + Athena)
-- ============================================================
create table if not exists modules (
  id               uuid default gen_random_uuid() primary key,
  company_id       uuid references companies(id),
  title            text not null,
  topic            text,
  order_index      integer not null default 0,
  duration_minutes integer default 20,
  source_documents text[],
  status           text check (status in ('pending_approval','active','inactive')) default 'pending_approval',
  created_at       timestamptz default now()
);

-- ============================================================
-- PROGRESO DEL EMPLEADO
-- ============================================================
create table if not exists employee_progress (
  id                  uuid default gen_random_uuid() primary key,
  employee_id         uuid references profiles(id),
  module_id           uuid references modules(id),
  status              text check (status in ('not_started','in_progress','completed')) default 'not_started',
  time_spent_minutes  integer default 0,
  started_at          timestamptz,
  completed_at        timestamptz,
  unique(employee_id, module_id)
);

-- ============================================================
-- HISTORIAL DE CHAT — Apollo + Atlas lo alimentan
-- ============================================================
create table if not exists chat_messages (
  id          uuid default gen_random_uuid() primary key,
  employee_id uuid references profiles(id),
  module_id   uuid references modules(id),
  role        text check (role in ('user','assistant')) not null,
  content     text not null,
  intent      text,   -- clasificación de Apollo (consulta, evento, dificultad, etc.)
  created_at  timestamptz default now()
);

-- ============================================================
-- PREGUNTAS DE QUIZ — generadas por Artemis
-- ============================================================
create table if not exists quiz_questions (
  id                  uuid default gen_random_uuid() primary key,
  module_id           uuid references modules(id),
  question            text not null,
  evaluation_criteria text,
  created_at          timestamptz default now()
);

-- ============================================================
-- RESULTADOS DE QUIZ — calificados por Artemis
-- ============================================================
create table if not exists quiz_results (
  id            uuid default gen_random_uuid() primary key,
  employee_id   uuid references profiles(id),
  question_id   uuid references quiz_questions(id),
  module_id     uuid references modules(id),
  answer        text not null,
  score         text check (score in ('correct','partial','incorrect')),
  justification text,
  created_at    timestamptz default now()
);

-- ============================================================
-- ANÁLISIS DE BRECHAS — producidos por Artemis
-- ============================================================
create table if not exists breach_analyses (
  id               uuid default gen_random_uuid() primary key,
  employee_id      uuid references profiles(id),
  module_id        uuid references modules(id),
  status           text check (status in ('verified','not_verified','breach_detected')),
  reason           text,
  suggested_action text,
  analyzed_at      timestamptz default now()
);

-- ============================================================
-- RLS: Row Level Security (aislamiento por empresa)
-- ============================================================
alter table companies          enable row level security;
alter table profiles           enable row level security;
alter table documents          enable row level security;
alter table document_chunks    enable row level security;
alter table modules            enable row level security;
alter table employee_progress  enable row level security;
alter table chat_messages      enable row level security;
alter table quiz_questions     enable row level security;
alter table quiz_results       enable row level security;
alter table breach_analyses    enable row level security;

create policy "perfil propio" on profiles
  for all using (auth.uid() = id);

create policy "documentos por empresa" on documents
  for all using (company_id = (select company_id from profiles where id = auth.uid()));

create policy "chunks por empresa" on document_chunks
  for all using (company_id = (select company_id from profiles where id = auth.uid()));

create policy "modulos por empresa" on modules
  for all using (company_id = (select company_id from profiles where id = auth.uid()));

create policy "progreso propio o supervisor" on employee_progress
  for all using (
    employee_id = auth.uid() or
    exists (select 1 from profiles where id = auth.uid() and role in ('admin','supervisor'))
  );

create policy "chat propio o supervisor" on chat_messages
  for all using (
    employee_id = auth.uid() or
    exists (select 1 from profiles where id = auth.uid() and role in ('admin','supervisor'))
  );

create policy "quiz questions por empresa" on quiz_questions
  for all using (
    exists (
      select 1 from modules m join profiles p on p.company_id = m.company_id
      where m.id = module_id and p.id = auth.uid()
    )
  );

create policy "quiz results propio o supervisor" on quiz_results
  for all using (
    employee_id = auth.uid() or
    exists (select 1 from profiles where id = auth.uid() and role in ('admin','supervisor'))
  );

create policy "analisis propio o supervisor" on breach_analyses
  for all using (
    employee_id = auth.uid() or
    exists (select 1 from profiles where id = auth.uid() and role in ('admin','supervisor'))
  );
