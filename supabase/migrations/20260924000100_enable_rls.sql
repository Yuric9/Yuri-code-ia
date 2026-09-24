-- Production uses direct PostgreSQL access from FastAPI. Enable RLS so the
-- public schema is not exposed to anonymous PostgREST access by default.
-- The backend's database role continues to work through direct SQLAlchemy access.
alter table public.projects enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.memories enable row level security;
alter table public.research_records enable row level security;
