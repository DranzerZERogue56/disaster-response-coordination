-- Migration 0009: two-factor sign-in for dispatchers.
--
-- Backlog B-07 / DEF-018 (docs/superpowers/plans/2026-11-15-two-factor-login.md). An account signs in with a password
-- AND a six-digit time-based code from an authenticator app on the person's own phone. This migration adds what the
-- sign-in needs to remember: the account's code secret, the last code step already used (so a code works once), a
-- failure counter and a lock time, and an append-only log of sign-in events. Passwords are never stored in plain form
-- (password_hash and password_salt already exist from migration 0001).

PRAGMA foreign_keys = ON;

ALTER TABLE dispatcher_accounts ADD COLUMN totp_secret TEXT;
ALTER TABLE dispatcher_accounts ADD COLUMN totp_last_step INTEGER;
ALTER TABLE dispatcher_accounts ADD COLUMN failed_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE dispatcher_accounts ADD COLUMN locked_until TEXT;

CREATE TABLE auth_events (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    at       TEXT NOT NULL,
    username TEXT NOT NULL,
    kind     TEXT NOT NULL CHECK (kind IN ('sign_in', 'sign_out', 'locked', 'enrolled')),
    ok       INTEGER NOT NULL CHECK (ok IN (0, 1)),
    detail   TEXT
);

CREATE INDEX idx_auth_events_user ON auth_events(username, at);

CREATE TRIGGER auth_events_no_edit
BEFORE UPDATE ON auth_events
BEGIN
    SELECT RAISE(ABORT, 'the sign-in event log is append-only');
END;
