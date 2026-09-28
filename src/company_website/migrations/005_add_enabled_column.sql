ALTER TABLE users ADD COLUMN enabled INTEGER DEFAULT 0;

UPDATE users SET enabled = 1 WHERE username = 'dev';
UPDATE users SET enabled = 0 WHERE username != 'dev';
