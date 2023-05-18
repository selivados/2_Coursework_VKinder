CREATE TABLE IF NOT EXISTS users (
    user_id      INTEGER     PRIMARY KEY,
    first_name   VARCHAR(40) NOT NULL,
    last_name    VARCHAR(40) NOT NULL,
    sex          INTEGER     NOT NULL,
    age          INTEGER     NOT NULL,
    city         VARCHAR(60) NOT NULL
);

CREATE TABLE IF NOT EXISTS photos (
    user_id   INTEGER PRIMARY KEY REFERENCES users (user_id),
    photo_ids TEXT    UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS favorite_list (
    PRIMARY KEY (user_id, partner_id),
    user_id    INTEGER REFERENCES users (user_id),
    partner_id INTEGER REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS black_list (
    PRIMARY KEY (user_id, partner_id),
    user_id    INTEGER REFERENCES users (user_id),
    partner_id INTEGER REFERENCES users (user_id)
);
