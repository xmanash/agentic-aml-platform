create table if not exists agent_traces (
  id uuid primary key default uuid_generate_v4(),
  case_id text not null,
  agent text not null,
  latency_ms float,
  tokens int default 0,
  decision text,
  created_at timestamptz default now()
);

alter table threshold_adjustments add column if not exists status text default 'applied';
alter table cases add column if not exists reason_codes jsonb;
alter table cases add column if not exists memory_hits jsonb;
alter table cases add column if not exists graph jsonb;
alter table cases add column if not exists confidence text;
alter table cases add column if not exists audit_hash text;
