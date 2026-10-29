
create extension if not exists "uuid-ossp";
create extension if not exists vector;

create table if not exists customers (id uuid primary key default uuid_generate_v4(), external_id text unique, full_name text not null, dob date, country text, risk_tier text default 'low', embedding vector(1536), created_at timestamptz default now());
create table if not exists accounts (id uuid primary key default uuid_generate_v4(), account_number text unique not null, customer_id uuid references customers(id), product text default 'payments', status text default 'active', created_at timestamptz default now());
create table if not exists transactions (id uuid primary key default uuid_generate_v4(), transaction_id text unique not null, account_id text not null, customer_id uuid references customers(id), amount numeric not null, currency text default 'USD', timestamp timestamptz not null, counterparty text, channel text default 'payments', type text default 'transfer', created_at timestamptz default now());
create table if not exists cases (id uuid primary key default uuid_generate_v4(), case_id text unique not null, risk_score float not null, status text not null, summary text, sar_draft text, entities jsonb, evidence jsonb, explanation jsonb, embedding vector(1536), created_at timestamptz default now());
create table if not exists entities (id uuid primary key default uuid_generate_v4(), entity_id text not null, case_id text references cases(case_id), type text, name text, linked_accounts text[], risk_score float, embedding vector(1536));
create table if not exists kyc_documents (id uuid primary key default uuid_generate_v4(), filename text, doc_type text, extracted_text text, extracted_fields jsonb, customer_id uuid references customers(id), storage_path text, created_at timestamptz default now());
create table if not exists audit_logs (id uuid primary key default uuid_generate_v4(), case_id text not null, agent text not null, action text not null, input_hash text, output_hash text, prev_hash text, hash text not null, payload jsonb, created_at timestamptz default now());
alter table audit_logs enable row level security;
create policy "allow_insert" on audit_logs for insert with check (true);
create policy "allow_select" on audit_logs for select using (true);
create table if not exists feedback (id uuid primary key default uuid_generate_v4(), case_id text not null, decision text not null, notes text, reviewer text, created_at timestamptz default now());
create table if not exists threshold_adjustments (id uuid primary key default uuid_generate_v4(), case_id text, key text, delta float, created_at timestamptz default now());
create table if not exists prompt_registry (id uuid primary key default uuid_generate_v4(), agent text, version int, prompt_text text, approved_by text, created_at timestamptz default now());
insert into customers (external_id, full_name, country, risk_tier) values ('CUST-BAD','Bad Actor LLC','RU','high'), ('CUST-OFF','Offshore Holdings','KY','high') on conflict (external_id) do nothing;
create or replace function match_cases(query_embedding vector(1536), match_count int) returns table (case_id text, similarity float) language sql as $$ select case_id, 1 - (embedding <=> query_embedding) as similarity from cases order by embedding <=> query_embedding limit match_count; $$;
