#!/usr/bin/env bash
# Idempotent dev setup: starts local PostgreSQL 16, creates the bodiq role/db + extensions.
set -euo pipefail
service postgresql start >/dev/null 2>&1 || true
for i in {1..15}; do pg_isready -q && break || sleep 1; done
su postgres -c "psql -tc \"select 1 from pg_roles where rolname='bodiq'\"" | grep -q 1 \
  || su postgres -c "psql -c \"create role bodiq login password 'bodiq_dev' createdb\""
su postgres -c "psql -tc \"select 1 from pg_database where datname='bodiq_dev'\"" | grep -q 1 \
  || su postgres -c "createdb -O bodiq bodiq_dev"
su postgres -c "psql -d bodiq_dev -qc 'create extension if not exists pg_trgm; create extension if not exists unaccent; create extension if not exists pgcrypto; create extension if not exists citext;'"
[ -f .env.local ] || { cp .env.example .env.local; sed -i "s/^AUTH_SECRET=.*/AUTH_SECRET=$(openssl rand -hex 32)/" .env.local; }
npm install --no-audit --no-fund
echo "dev environment ready"
