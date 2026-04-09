# Lead Generation Security

This folder contains access rules for the Lead Generation model.

## Access File

- `ir.model.access.csv`

## Rules

- `lead.generation`: user can read/write/create (no unlink), system full
- `lead.activity`: user read-only, system full
- `lead.api.token`: system full
- `lead.webhook`: system full

## Notes

The API uses `sudo()` for testing, so it bypasses these rules. For production, remove `sudo()` and enforce proper access control.
