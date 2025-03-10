-- Create users
CREATE USER activity_user WITH PASSWORD 'LL9TgAjw3Ca4pCJ';
CREATE USER analytics_user WITH PASSWORD '103QKa3O4kpDnZA';

-- Grant privileges on databases
GRANT ALL PRIVILEGES ON DATABASE activity_service TO activity_user;
GRANT ALL PRIVILEGES ON DATABASE analytics_service TO analytics_user;

-- Switch to activity_service and grant schema-level permissions
\c activity_service;

GRANT USAGE ON SCHEMA public TO activity_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO activity_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO activity_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO activity_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO activity_user;

-- Switch to analytics_service and grant schema-level permissions
\c analytics_service;

GRANT USAGE ON SCHEMA public TO analytics_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO analytics_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO analytics_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO analytics_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO analytics_user;
