# Lead Generation API Guide

This module adds a Lead Generation model and REST-style API endpoints.

## Run Odoo (VS Code / PowerShell)

From `D:\Internship\Project\odoo_test`:

```powershell
.\venv\Scripts\Activate.ps1
python odoo-bin
```

If you change code, upgrade the module:

```powershell
python odoo-bin -u lead_generation -d odoo
```

## API Endpoints

Base URL: `http://localhost:8069`

- `POST /api/leads` - Create lead
- `GET /api/leads` - List leads (pagination and filters)
- `GET /api/leads/<id>` - Get one lead
- `PUT /api/leads/<id>` - Update lead
- `DELETE /api/leads/<id>` - Archive lead

## Postman Setup

1. Method: `POST`
2. URL: `http://localhost:8069/api/leads`
3. Headers:
   - `Content-Type: application/json`
4. Body: **raw** -> **JSON**

Example JSON:

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

Expected response:

```json
{
  "status": "success",
  "data": {
    "id": 4,
    "name": "Rajesh Kumar",
    "email": "rajesh@example.com",
    "status": "new"
  },
  "message": "Lead created successfully"
}
```

## PowerShell API Test

```powershell
$body = @{
  name = "Rajesh Kumar"
  email = "rajesh@example.com"
  phone = "+91-9876543210"
  company = "Tech Solutions"
  lead_source = "website"
  budget = 100000
  notes = "Test lead from API"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8069/api/leads" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

## Common Errors and Fixes

### 1) `ModuleNotFoundError: No module named 'babel'`
Cause: using system Python instead of venv.
Fix:
```powershell
.\venv\Scripts\Activate.ps1
python odoo-bin -u lead_generation -d odoo
```

### 2) PostgreSQL collation error
```
FATAL: collations with different collate and ctype values are not supported
```
Fix (recreate DB):
```powershell
& "C:\Program Files\PostgreSQL\18\bin\dropdb.exe" -U odoo odoo
& "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -U odoo -E UTF8 -l C -T template0 odoo
```

### 3) `MISSING_NAME`
Your JSON body is empty or missing `name`.

### 4) `DUPLICATE_EMAIL`
Lead with same email already exists. Use a new email or update the existing lead.

## Notes
- Custom modules live in `custom_addons/`.
- Addons path must include `custom_addons` in `odoo.conf`.
- The API is public for testing and uses `sudo()` to bypass access rules.
