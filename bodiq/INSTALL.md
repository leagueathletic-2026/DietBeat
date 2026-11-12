# BODIQ — Installed toolchain

| Layer | Package / tool | Notes |
|---|---|---|
| App | Next.js 16, React 19, TypeScript 5, Tailwind 4 | App Router, `src/` layout |
| Database | PostgreSQL 16 (local dev) → Supabase Postgres (prod) | via `DATABASE_URL`, `postgres` driver; extensions `pg_trgm`, `unaccent`, `pgcrypto`, `citext` |
| Auth | `jose` (signed cookies/JWT) | client access codes + admin login |
| Validation | `zod` 4 | |
| AI | `@anthropic-ai/sdk` | server-side only |
| UI | `lucide-react`, `framer-motion` | |
| Barcode | `@zxing/browser`, `@zxing/library` | browser-only (Node warning is harmless) |
| CSV | `papaparse` | import/export |
| PDF | `jspdf` | meal download |
| PWA | `serwist`, `@serwist/next` | |
| Images | `sharp` | |
| Tests | `vitest`, Playwright (preinstalled in the container) | |

## Commands
- `./scripts/dev-setup.sh` — start Postgres, create DB, install deps
- `npm run dev | build | test | lint | typecheck | db:check`

## Still needed from you (not installable)
USDA key (free), Google Places key, Tavily/Exa key, Anthropic key, Supabase project (+ host allow-listing). See `.env.example`.
