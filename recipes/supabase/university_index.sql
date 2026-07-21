-- Reference Supabase/PostgreSQL foundation for the generated ROR seed.
-- Apply this before the output of scripts/build_university_seed_sql.py.

begin;

create schema if not exists extensions;
create extension if not exists pg_trgm with schema extensions;
create extension if not exists unaccent with schema extensions;

create table public.university_index (
  ror_id text primary key,
  priority integer not null unique,
  ranking_score double precision not null,
  display_name text not null,
  normalized_name text not null,
  search_names text[] not null,
  acronyms text[] not null default array[]::text[],
  aliases text[] not null default array[]::text[],
  labels text[] not null default array[]::text[],
  domains text[] not null default array[]::text[],
  search_text text not null,
  country text not null,
  country_code text not null,
  city text not null,
  admin_name text not null default '',
  geonames_id bigint not null,
  lat double precision not null,
  lng double precision not null,
  established integer,
  organization_types text[] not null,
  website text not null default '',
  source_release text not null,
  constraint university_index_ror_id_check
    check (ror_id ~ '^https://ror[.]org/[a-z0-9]{9}$'),
  constraint university_index_priority_check check (priority >= 0),
  constraint university_index_ranking_score_check check (ranking_score >= 0),
  constraint university_index_display_name_check
    check (char_length(display_name) between 1 and 240),
  constraint university_index_normalized_name_check
    check (char_length(normalized_name) between 1 and 240),
  constraint university_index_search_names_check
    check (cardinality(search_names) between 1 and 32),
  constraint university_index_search_text_check
    check (char_length(search_text) between 1 and 4000),
  constraint university_index_country_check
    check (char_length(country) between 1 and 160),
  constraint university_index_country_code_check
    check (country_code ~ '^[A-Z]{2}$'),
  constraint university_index_city_check
    check (char_length(city) between 1 and 160),
  constraint university_index_coordinates_check
    check (lat between -90 and 90 and lng between -180 and 180),
  constraint university_index_established_check
    check (established is null or established between 1 and 3000),
  constraint university_index_types_check
    check ('education' = any(organization_types)),
  constraint university_index_source_release_check
    check (char_length(source_release) between 1 and 80)
);

comment on table public.university_index is
  'ROR-backed active education organizations for bounded university autocomplete.';

create index university_index_search_text_trgm_idx
on public.university_index
using gin (search_text extensions.gin_trgm_ops);

create index university_index_normalized_name_prefix_idx
on public.university_index (normalized_name text_pattern_ops);

create index university_index_search_names_idx
on public.university_index
using gin (search_names);

create index university_index_domains_idx
on public.university_index
using gin (domains);

create or replace function public.normalize_university_search_text_v1(
  p_value text
)
returns text
language sql
immutable
strict
set search_path = ''
as $$
  select btrim(
    regexp_replace(
      extensions.unaccent(lower(p_value)),
      '[[:space:][:punct:]]+',
      ' ',
      'g'
    )
  )
$$;

create or replace function public.search_university_suggestions_v1(
  p_query text,
  p_limit integer default 10
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
set row_security = off
as $$
declare
  raw_query text := btrim(coalesce(p_query, ''));
  normalized_query text;
  escaped_query text;
  bounded_limit integer := least(greatest(coalesce(p_limit, 10), 1), 12);
begin
  if char_length(raw_query) not between 2 and 120 then
    raise exception using
      errcode = '22023',
      message = 'invalid_university_query';
  end if;

  normalized_query := public.normalize_university_search_text_v1(raw_query);
  if char_length(normalized_query) < 2 then
    raise exception using
      errcode = '22023',
      message = 'invalid_university_query';
  end if;

  escaped_query := replace(
    replace(replace(normalized_query, '\', '\\'), '%', '\%'),
    '_',
    '\_'
  );

  return jsonb_build_object(
    'items',
    coalesce((
      select jsonb_agg(
        jsonb_build_object(
          'rorId', university.ror_id,
          'displayName', university.display_name,
          'acronyms', university.acronyms,
          'country', university.country,
          'countryCode', university.country_code,
          'city', university.city,
          'website', nullif(university.website, '')
        )
        order by university.match_tier, university.priority
      )
      from (
        select
          candidate.*,
          case
            when normalized_query = any(candidate.search_names) then 0
            when exists (
              select 1
              from unnest(candidate.domains) as domain(value)
              where public.normalize_university_search_text_v1(domain.value)
                = normalized_query
            ) then 0
            when candidate.normalized_name
              like escaped_query || '%' escape '\' then 1
            when exists (
              select 1
              from unnest(candidate.search_names) as name(value)
              where name.value like escaped_query || '%' escape '\'
            ) then 1
            when exists (
              select 1
              from unnest(candidate.search_names) as name(value)
              where position(' ' || normalized_query in ' ' || name.value) > 0
            ) then 2
            else 3
          end as match_tier
        from public.university_index as candidate
        where candidate.search_text
          like '%' || escaped_query || '%' escape '\'
        order by match_tier, candidate.priority, candidate.display_name
        limit bounded_limit
      ) as university
    ), '[]'::jsonb)
  );
end;
$$;

alter table public.university_index enable row level security;
alter table public.university_index force row level security;

create policy university_index_service_role_all
on public.university_index
to service_role
using (true)
with check (true);

revoke all on table public.university_index
from public, anon, authenticated, service_role;
grant all on table public.university_index to service_role;

revoke all on function public.normalize_university_search_text_v1(text)
from public, anon, authenticated, service_role;
grant execute on function public.normalize_university_search_text_v1(text)
to service_role;

revoke all on function public.search_university_suggestions_v1(text, integer)
from public, anon, authenticated, service_role;
grant execute on function public.search_university_suggestions_v1(text, integer)
to anon, authenticated, service_role;

commit;
