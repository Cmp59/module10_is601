-- Module 9 users have no passwords. Keep their accounts without a hash until
-- a secure password setup process is implemented; never invent a password.
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
