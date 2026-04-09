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

- `POST /api/auth/token` - Create API token (email + password)
- `POST /api/leads` - Create lead (token required)
- `GET /api/leads` - List leads (token required)
- `GET /api/leads/<id>` - Get one lead (token required)
- `PUT /api/leads/<id>` - Update lead (token required)
- `DELETE /api/leads/<id>` - Archive lead (admin token)
- `PUT /api/leads/bulk/update` - Bulk update (write token)
- `GET /api/leads/analytics` - Analytics (token required)

## Postman Setup (Token)

1. Method: `POST`
2. URL: `http://localhost:8069/api/auth/token`
3. Headers:
   - `Content-Type: application/json`
4. Body: **raw** -> **JSON**

Token request JSON:

```json
{
  "email": "admin",
  "password": "admin",
  "scope": "write"
}
```

Expected response (token):

```json
{
  "status": "success",
  "data": {
    "token": "...",
    "expires_at": "...",
    "scope": "write"
  }
}

## Postman Setup (Create Lead)

1. Method: `POST`
2. URL: `http://localhost:8069/api/leads`
3. Headers:
   - `Content-Type: application/json`
   - `Authorization: Bearer <token>`
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
  -Headers @{ Authorization = "Bearer <token>" } `
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

### 5) `MISSING_TOKEN`
API requests require `Authorization: Bearer <token>`.

### 6) `PERMISSION_DENIED`
Token has `read` scope. Use a `write` or `admin` token.

## Notes
- Custom modules live in `custom_addons/`.
- Addons path must include `custom_addons` in `odoo.conf`.
- The API is public for testing and uses `sudo()` to bypass access rules.
