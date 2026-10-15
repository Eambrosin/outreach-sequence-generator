-- Ambrosin Commercial Mandate Workspace
-- Run this in the Supabase SQL editor for the private workspace project.
-- The tables intentionally use RLS with no public policies.
-- Server-side access should use a Supabase Secret key (sb_secret_...), or the
-- legacy service_role key if required, stored only in Streamlit secrets.
-- Never commit that key to GitHub or expose it client-side.

create table if not exists public.commercial_mandates (
    mandate_id text primary key,
    mandate_name text not null default '',
    mandate_status text not null default 'Active',
    mandate_client text not null default '',
    mandate_target_market text not null default '',
    mandate_product text not null default '',
    source_stage text not null default '',
    payload jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
);

create index if not exists commercial_mandates_status_idx
    on public.commercial_mandates (mandate_status);

create index if not exists commercial_mandates_updated_at_idx
    on public.commercial_mandates (updated_at desc);

create table if not exists public.commercial_workspaces (
    workspace_id text primary key,
    mandate_id text not null
        references public.commercial_mandates (mandate_id)
        on delete cascade,
    workspace_name text not null default '',
    payload jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
);

create index if not exists commercial_workspaces_mandate_id_idx
    on public.commercial_workspaces (mandate_id);

create index if not exists commercial_workspaces_updated_at_idx
    on public.commercial_workspaces (updated_at desc);

alter table public.commercial_mandates enable row level security;
alter table public.commercial_workspaces enable row level security;

-- No anon/authenticated policies are created intentionally.
-- A server-side service-role key bypasses RLS and keeps these commercial
-- records inaccessible through the public Supabase API role.


grant select, insert, update, delete
    on table public.commercial_mandates
    to service_role;

grant select, insert, update, delete
    on table public.commercial_workspaces
    to service_role;


revoke all privileges on table public.commercial_mandates from anon, authenticated;
revoke all privileges on table public.commercial_workspaces from anon, authenticated;
