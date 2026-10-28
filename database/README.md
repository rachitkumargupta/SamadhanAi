# Database setup

## Environment

The local setup used PostgreSQL 18.6 on Windows. The project requirements specify SQLAlchemy 2.x and `psycopg[binary]`. The backend reads the connection string from `DATABASE_URL`.

## Extensions

The local database uses `pgcrypto` and `vector`. The pgvector server files must be installed for the installed PostgreSQL version before enabling the extension.

Run in pgAdmin Query Tool connected to the intended database:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
```

Verify installed extensions:

```sql
SELECT extname
FROM pg_extension
WHERE extname IN ('pgcrypto', 'vector')
ORDER BY extname;
```

## Connection string

Use this pattern for the `psycopg` v3 driver:

```text
postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/DATABASE_NAME
```

Set the real value in `.env`, not in a committed file. URL-encode reserved characters in passwords where necessary.

## Important migration warning

This local database was created and adjusted manually while the repository also contains Alembic migrations. Do not run `alembic upgrade head` against this database until migration history and existing objects are reconciled. A successful connection does not prove every application operation is compatible.



## Important migration warning

This local database was created and adjusted manually while the repository also contains Alembic migrations. Do not run `alembic upgrade head` against this database until migration history and existing objects are reconciled. A successful connection does not prove every application operation is compatible.

The current package does not include a full table-creation script. Before treating the database as reproducible, export and review the actual schema, reconcile it with the final ER diagram and backend models, then commit the agreed schema or migrations and test them against a fresh, disposable database.
