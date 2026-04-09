# Lead Generation Models

This folder contains the ORM model for the Lead Generation module.

## Model File

- `lead.py`

## Model: `lead.generation`

Purpose: stores lead records for the custom Lead Generation app.

Key fields:
- `name` (Char, required) - Lead name
- `email` (Char, required) - Lead email
- `phone` (Char) - Phone number
- `company` (Char) - Company name
- `lead_source` (Selection) - Source of lead
- `status` (Selection) - Lead pipeline status
- `budget` (Float) - Budget amount
- `expected_closing_date` (Date) - Expected close date
- `notes` (Text) - Notes
- `active` (Boolean) - Archive flag

Sorting:
- `_order = 'create_date desc'`

## Notes

Selection values must match those used by the API and UI. For example, valid `lead_source` values include:
- `website`, `phone`, `email`, `social_media`, `referral`, `walk_in`, `other`
