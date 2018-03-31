---
CREATE TABLE redirects (
    id serial PRIMARY KEY,
    created_at timestamp DEFAULT now(),
    short_url text NOT NULL,
    original_url text NOT NULL
);

CREATE INDEX short_url_idx ON redirects (short_url);
