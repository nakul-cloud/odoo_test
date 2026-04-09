# Lead Generation Views

This folder contains the UI definitions for the Lead Generation app.

## View Files

- `lead_views.xml`
- `lead_api_token_views.xml`
- `lead_activity_views.xml`
- `lead_webhook_views.xml`

## Contents

- Form view for `lead.generation`
- List view (uses `<list>` for Odoo 19)
- Search view with filters and group-by filters
- Admin menus for API Tokens, Activity Log, Webhooks

## Notes

In Odoo 19, list views use `<list>` instead of `<tree>`. The action uses `view_mode="list,form"`.
