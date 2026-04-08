# Project Workflow and Setup Notes

## Overview
This repository is an Odoo 19.0 server with custom modules stored in a separate folder. The main custom module created is `lead_generation`, located in `custom_addons/lead_generation`.

## Folder Layout
- `odoo/` - Core Odoo framework
- `addons/` - Standard Odoo addons
- `custom_addons/` - Custom addons created for this project
- `odoo.conf` - Odoo configuration
- `requirements.txt` - Python dependencies

## Custom Addon: lead_generation

### Goal
Create a custom lead management module that follows Odoo 19 conventions and uses a dedicated custom addons folder.

### Module Structure
```
custom_addons/lead_generation/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── __init__.py
│   └── lead.py
├── views/
│   └── lead_views.xml
└── security/
    └── ir.model.access.csv
```

### Key Model
- Model: `lead.generation`
- Fields: name, email, phone, company, lead_source, status, budget, expected_closing_date, notes, active

### Views
- Form, list, search views
- Menu: Lead Generation -> Leads

### Odoo 19 XML Update
Odoo 19 uses `<list>` instead of `<tree>` for list views. We updated:
- `<tree>` to `<list>` in list view
- `view_mode` from `tree,form` to `list,form`
- Simplified search view group-by filters to avoid invalid XML in Odoo 19

## Configuration Changes

### Addons Path
The `odoo.conf` file was updated to load custom modules from `custom_addons`:
```
addons_path = d:\Internship\Project\odoo_test\custom_addons,d:\Internship\Project\odoo_test\addons,d:\Internship\Project\odoo_test\odoo\addons
```

## Database Issues and Fix

### Error
PostgreSQL threw:
```
FATAL: collations with different collate and ctype values are not supported on this platform
```

### Root Cause
The `odoo` database was created with mismatched collation settings on Windows.

### Fix
We dropped and recreated the database using a consistent locale and encoding:
```
"C:\Program Files\PostgreSQL\18\bin\dropdb.exe" -U odoo odoo
"C:\Program Files\PostgreSQL\18\bin\createdb.exe" -U odoo -E UTF8 -l C -T template0 odoo
```

Verification query:
```
SELECT datname, datcollate, datctype FROM pg_database WHERE datname='odoo';
```
Expected output:
```
odoo | C | C
```

## Module Installation
After fixing the database, the module was installed via:
```
.\venv\Scripts\python.exe odoo-bin -i lead_generation -d odoo
```

## Running Odoo
```
.\venv\Scripts\python.exe odoo-bin
```
Then open:
```
http://localhost:8069
```

## Git Workflow
We committed each major file or step, including:
- Module manifest
- Init files
- Model
- Security rules
- Views
- Odoo 19 view fixes

All changes were pushed to:
```
https://github.com/nakul-cloud/odoo_test.git
```
