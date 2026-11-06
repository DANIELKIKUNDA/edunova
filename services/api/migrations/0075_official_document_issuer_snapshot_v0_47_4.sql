ALTER TABLE official_documents ADD COLUMN issuer_name VARCHAR(240);
ALTER TABLE official_documents ADD COLUMN issuer_legal_name VARCHAR(240);
ALTER TABLE official_documents ADD COLUMN issuer_country_code VARCHAR(2);
ALTER TABLE official_documents ADD COLUMN template_version VARCHAR(40) NOT NULL DEFAULT 'official-v1';
