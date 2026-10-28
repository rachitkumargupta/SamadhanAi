-- Read-only verification queries. Run against the intended development database.

-- 1. Current database
SELECT current_database() AS database_name;

-- 2. Number and names of public base tables
SELECT COUNT(*) AS public_table_count
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE';

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- 3. Required extensions
SELECT extname
FROM pg_extension
WHERE extname IN ('pgcrypto', 'vector')
ORDER BY extname;

-- 4. Confirm the embedding type, if the table/column exists
SELECT table_name, column_name, data_type, udt_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'knowledge_chunks'
  AND column_name = 'embedding';
