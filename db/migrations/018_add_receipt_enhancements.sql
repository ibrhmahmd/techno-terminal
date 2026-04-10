-- Migration 018: Add Receipt Enhancements
-- Created: 2026-04-08
-- Purpose: Enhance receipts table with template support and delivery tracking

-- Add new columns to receipts table
ALTER TABLE receipts 
    ADD COLUMN IF NOT EXISTS receipt_template VARCHAR(50) DEFAULT 'standard',
    ADD COLUMN IF NOT EXISTS auto_generated BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS sent_to_parent BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS parent_email VARCHAR(255),
    ADD COLUMN IF NOT EXISTS generation_metadata JSONB;  -- Store template vars, generation params

-- Create index for receipt template queries
CREATE INDEX idx_receipts_template ON receipts(receipt_template);
CREATE INDEX idx_receipts_auto_generated ON receipts(auto_generated) WHERE auto_generated = TRUE;
CREATE INDEX idx_receipts_sent ON receipts(sent_to_parent) WHERE sent_to_parent = FALSE;

-- Create generated receipts table (stores rendered receipt content)
CREATE TABLE IF NOT EXISTS generated_receipts (
    id SERIAL PRIMARY KEY,
    receipt_id INTEGER NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
    template_used VARCHAR(50) NOT NULL,
    content_format VARCHAR(20) NOT NULL DEFAULT 'text',  -- 'text', 'html', 'pdf'
    content TEXT NOT NULL,
    file_path VARCHAR(500),  -- If stored as file
    file_size INTEGER,
    checksum VARCHAR(64),  -- For integrity verification
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    generated_by INTEGER REFERENCES users(id),
    expires_at TIMESTAMPTZ  -- For temporary receipts
);

CREATE INDEX idx_generated_receipts_receipt ON generated_receipts(receipt_id);
CREATE INDEX idx_generated_receipts_format ON generated_receipts(content_format);
CREATE INDEX idx_generated_receipts_generated_at ON generated_receipts(generated_at);

-- Create receipt templates table (for custom templates)
CREATE TABLE IF NOT EXISTS receipt_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(50) UNIQUE NOT NULL,
    template_type VARCHAR(20) NOT NULL DEFAULT 'standard',  -- 'standard', 'detailed', 'summary', 'refund'
    format VARCHAR(20) NOT NULL DEFAULT 'text',  -- 'text', 'html', 'markdown'
    content TEXT NOT NULL,
    header_template TEXT,
    footer_template TEXT,
    css_styles TEXT,  -- For HTML templates
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_receipt_templates_active ON receipt_templates(is_active, is_default) WHERE is_active = TRUE;

-- Insert default receipt templates
INSERT INTO receipt_templates (template_name, template_type, format, content, is_default, is_active)
VALUES (
    'standard',
    'standard',
    'text',
    '========================================
RECEIPT #: {{ receipt_number }}
Date: {{ paid_at }}
========================================

Student: {{ student_name }}
Payer: {{ payer_name }}

----------------------------------------
DESCRIPTION                    AMOUNT
----------------------------------------
{% for line in payment_lines %}
{{ line.description }} {{ line.amount }}
{% endfor %}
----------------------------------------
Subtotal:                      {{ subtotal }}
Discount:                      {{ total_discount }}
----------------------------------------
TOTAL PAID:                    {{ total }}
----------------------------------------

Payment Method: {{ payment_method }}
Received By: {{ received_by }}

{% if balance_remaining > 0 %}
Remaining Balance: {{ balance_remaining }}
{% endif %}

Thank you for your payment!
========================================',
    TRUE,
    TRUE
)
ON CONFLICT (template_name) DO NOTHING;
