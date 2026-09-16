# Deploying

Both halves run on Vercel, with Postgres on Neon. All free, no card needed.

One repo, two Vercel projects — they differ only by Root Directory.

## 1. Database (Neon)

1. Sign up at [neon.tech](https://neon.tech) and create a project.
2. Copy **both** connection strings from the dashboard:
   - the **pooled** one (host contains `-pooler`) — for the app
   - the **direct** one — for migrations
3. Change the scheme on both from `postgresql://` to `postgresql+psycopg://`.
   SQLAlchemy needs the driver named and will fail at startup without it.

Two URLs because serverless functions open a connection per invocation, so the app
must go through Neon's pooler. Migrations run DDL, which a transaction pooler won't
reliably pass, so they use the direct host.

## 2. Backend (Vercel)

New Project → same repo → **Root Directory: `backend`**.

Environment variables:

| Variable | Value |
|---|---|
| `ANTHROPIC_API_KEY` | from [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| `DATABASE_URL` | Neon **pooled** string |
| `JWT_SECRET` | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `SERVERLESS` | `true` |
| `CORS_ORIGINS` | `["https://<frontend-project>.vercel.app"]` |
| `ENVIRONMENT` | `production` |
| `LOG_JSON` | `true` |

`SERVERLESS=true` switches SQLAlchemy to `NullPool`. Without it the app holds
connections across invocations that are never reused or cleanly closed, and Neon
starts refusing new ones.

The app refuses to start if `JWT_SECRET` is under 32 bytes or still says `change-me`.

### Migrations

`pyproject.toml` sets a build script that runs `alembic upgrade head` on every deploy.
It is idempotent, so repeat deploys are harmless.

Because the build uses `DATABASE_URL`, and that variable holds the *pooled* host, run
the first migration by hand against the direct host instead:

```bash
cd backend
DATABASE_URL="<direct neon url>" uv run python scripts/migrate.py
```

## 3. Frontend (Vercel)

New Project → same repo → **Root Directory: `frontend`**.

| Variable | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://<backend-project>.vercel.app/api/v1` |

Vite bakes environment variables in at build time, so changing this needs a
**redeploy**, not a restart.

Then go back and set `CORS_ORIGINS` on the backend to this project's exact origin —
no trailing slash. Until that matches, the browser blocks every request.

## 4. Make it reachable

Settings → Deployment Protection → turn off Vercel Authentication on both projects.
Branch-preview URLs (`<project>-git-main-…`) are gated by default, so anyone you send
one to sees a Vercel login page rather than the app.

Use the production domain, `<project>.vercel.app`.

## 5. Check it

```bash
curl https://<backend-project>.vercel.app/health
```

Then open the frontend, create an account, and run a screening.

## Known rough edges

**Spend.** Both Claude calls sit behind an interviewer account, so nobody can run up
the bill without signing up — but signup is open to anyone with the URL. Set a budget
cap in the Anthropic console.

**Cold starts.** Shorter than a container host, but the first request after idle still
pays for import and connection setup before the 30–90s Claude call begins.

**Bundle size.** ~650 KB (205 KB gzipped), mostly MUI. Worth code-splitting before this
sees real traffic.

## Running it on a container host instead

`backend/Dockerfile` and `render.yaml` are still here and still work. On a long-lived
host leave `SERVERLESS` unset, use the direct Neon URL, and migrations run on boot from
the Dockerfile's `CMD` rather than needing a separate step.
