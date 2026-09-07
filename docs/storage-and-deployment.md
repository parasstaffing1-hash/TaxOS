# Storage and production database

## Cloudflare R2

TaxOS uses the S3-compatible R2 API for uploaded tax documents and generated
analytics reports. Create a private bucket and an R2 API token with Object Read
& Write permission scoped to that bucket. The application uses the `auto`
region required by R2.

Set these values in the server-side `.env` file:

```env
STORAGE_BACKEND=r2
R2_ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
R2_BUCKET=taxos-documents
R2_ACCESS_KEY_ID=<R2_ACCESS_KEY_ID>
R2_SECRET_ACCESS_KEY=<R2_SECRET_ACCESS_KEY>
```

Keep the bucket private. Tax documents can contain PAN, Aadhaar, salary,
invoice, and bank information. Configure an R2 lifecycle policy for retention
and delete access when a customer requests removal. Do not commit the `.env`
file or R2 credentials.

Development and tests use `STORAGE_BACKEND=local` and write under `.storage/`.

## Aiven PostgreSQL

Aiven PostgreSQL works with the existing SQLAlchemy `asyncpg` driver. Copy the
connection string from the Aiven service overview, use the
`postgresql+asyncpg://` scheme, and keep SSL enabled:

```env
DATABASE_URL=postgresql+asyncpg://<USER>:<PASSWORD>@<HOST>:<PORT>/<DATABASE>?sslmode=require
```

The application also normalizes Aiven URLs using the `postgres://` or plain
`postgresql://` schemes. When launching with the provided Docker Compose file,
set `TAXOS_DATABASE_URL` to the Aiven URL; leaving it blank uses the bundled
PostgreSQL container. For a direct API deployment, set `DATABASE_URL` instead.

For stricter certificate verification, provide the Aiven CA certificate and
configure the connection with `verify-ca` or `verify-full` according to your
hosting environment. Restrict the Aiven service IP allowlist to the API host.

The API container runs `alembic upgrade head` before Uvicorn starts. For a
multi-replica deployment, run migrations once as a release step before starting
all API replicas.
