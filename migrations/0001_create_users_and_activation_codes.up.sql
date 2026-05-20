CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    password    TEXT        NOT NULL,
    email       TEXT        NOT NULL UNIQUE,
    is_active   BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS activation_codes (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER     NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    code        CHAR(4)     NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
