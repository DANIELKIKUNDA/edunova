CREATE TABLE campus_commercial_offers (
 code varchar(64) PRIMARY KEY,
 label varchar(160) NOT NULL,
 price_cdf integer NOT NULL CHECK (price_cdf >= 0),
 seats integer NOT NULL CHECK (seats BETWEEN 1 AND 100000),
 duration_days integer NOT NULL CHECK (duration_days BETWEEN 1 AND 3660),
 grace_days integer NOT NULL CHECK (grace_days BETWEEN 0 AND 90),
 active boolean NOT NULL DEFAULT false,
 revision integer NOT NULL CHECK (revision >= 1),
 updated_by varchar(64) NOT NULL,
 updated_at timestamptz NOT NULL
);
