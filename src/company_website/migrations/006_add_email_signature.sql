ALTER TABLE users ADD COLUMN email_signature TEXT NOT NULL DEFAULT 'Best regards,
{{ firstname }} {{ lastname }}
{{ role }}
{{ company }}';
