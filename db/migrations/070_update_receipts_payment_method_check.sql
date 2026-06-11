-- Migration 070: Update Receipts Payment Method Check Constraint
-- Created: 2026-06-11
-- Purpose: Update receipts_payment_method_check constraint to support ewallet, instapay, and other payment methods.

ALTER TABLE receipts
    DROP CONSTRAINT IF EXISTS receipts_payment_method_check,
    ADD CONSTRAINT receipts_payment_method_check
        CHECK (payment_method = ANY (ARRAY['cash'::text, 'card'::text, 'transfer'::text, 'online'::text, 'ewallet'::text, 'instapay'::text, 'other'::text]));
