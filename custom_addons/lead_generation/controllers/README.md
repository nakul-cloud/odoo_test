# Lead Generation Controllers Guide

This folder contains REST-style API endpoints for the Lead Generation module.

## Controllers

File: `lead_api.py`

Routes (base URL: `http://localhost:8069`):
- `POST /api/leads` - Create a lead
- `GET /api/leads` - List leads (pagination + filters)
- `GET /api/leads/<id>` - Get one lead
- `PUT /api/leads/<id>` - Update a lead
- `DELETE /api/leads/<id>` - Archive a lead

Response format:
```
{
  "status": "success|error",
  "data": {...},
  "message": "..."
}
```

### Error handling used in controllers

- `MISSING_NAME` - Missing `name` field
- `MISSING_EMAIL` - Missing `email` field
- `DUPLICATE_EMAIL` - Email already exists
- `INVALID_PARAMETER` - Bad pagination values
- `NOT_FOUND` - Lead id not found
- `SERVER_ERROR` - Unhandled exception

Implementation details:
- Uses `request.make_response(...)` for JSON output.
- Uses `sudo()` to allow public access for testing.
- Ensures a database is selected for public requests (`request.session.db`).

## Models

File: `../models/lead.py`

Model: `lead.generation`

Key fields:
- `name` (required)
- `email` (required)
- `phone`, `company`
- `lead_source` (Selection)
- `status` (Selection)
- `budget`, `expected_closing_date`, `notes`
- `active`

## Views

File: `../views/lead_views.xml`

- Form view
- List view (Odoo 19 uses `<list>`)
- Search view with filters
- Menu: Lead Generation -> Leads

## Security

File: `../security/ir.model.access.csv`

Access rules:
- `base.group_user`: read/write/create (no unlink)
- `base.group_system`: full access

## Postman Quick Test

Headers:
- `Content-Type: application/json`

Body (raw JSON):
```json
{
  "name": "Rajesh Kumar",
  "email": "rajesh@example.com",
  "phone": "+91-9876543210",
  "company": "Tech Solutions",
  "lead_source": "website",
  "budget": 100000,
  "notes": "Test lead from API"
}
```

Expected success response:
```
{
  "status": "success",
  "data": {"id": 4, "name": "Rajesh Kumar", "email": "rajesh@example.com", "status": "new"},
  "message": "Lead created successfully"
}
```
