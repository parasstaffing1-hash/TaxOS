#!/bin/sh
set -eu

# Apply the schema before accepting requests. Alembic makes this safe for a
# freshly provisioned database as well as an already-upgraded deployment.
alembic upgrade head

exec "$@"
