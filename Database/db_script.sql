CREATE TABLE IF NOT EXISTS users (
    user_id    INTEGER     PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name  VARCHAR(50) NOT NULL,
    sex        INTEGER     NOT NULL,
    age        INTEGER     NOT NULL,
    city       VARCHAR(50) NOT NULL,
    CONSTRAINT valid_sex CHECK (sex IN (1, 2)),
    CONSTRAINT valid_age CHECK (age > 0)
);

CREATE TABLE IF NOT EXISTS photos (
    photo_id INTEGER PRIMARY KEY,
    user_id  INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS favorite_partners (
    user_id    INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    partner_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT favorite_partners_pkey PRIMARY KEY (user_id, partner_id),
    CONSTRAINT favorite_not_self CHECK (user_id != partner_id)
);

CREATE TABLE IF NOT EXISTS blocked_partners (
    user_id    INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    partner_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT blocked_partners_pkey PRIMARY KEY (user_id, partner_id),
    CONSTRAINT blocked_not_self CHECK (user_id != partner_id)
);
