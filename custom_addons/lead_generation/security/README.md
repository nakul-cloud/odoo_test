# Lead Generation Security

This folder contains access rules for the Lead Generation model.

## Access File

- `ir.model.access.csv`

## Rules

- `base.group_user`: read/write/create (no unlink)
- `base.group_system`: full access

## Notes

The API uses `sudo()` for testing, so it bypasses these rules. For production, remove `sudo()` and enforce proper access control.
