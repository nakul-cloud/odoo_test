import json
import logging
import requests
import hmac
import hashlib
from datetime import timedelta, date
from functools import wraps

from odoo import http, fields
from odoo.http import request
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


def token_required(func):
    """Require a valid API token in the Authorization header."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        header = request.httprequest.headers.get('Authorization', '')
        token_value = header.replace('Bearer ', '').strip()

        if not token_value:
            return args[0]._json_response({
                'status': 'error',
                'error_code': 'MISSING_TOKEN',
                'message': 'API token required'
            }, status=401)

        token_obj = request.env['lead.api.token'].sudo().search([
            ('token', '=', token_value)
        ], limit=1)

        if not token_obj or not token_obj.verify_token(token_value):
            return args[0]._json_response({
                'status': 'error',
                'error_code': 'INVALID_TOKEN',
                'message': 'Invalid or expired token'
            }, status=403)

        token_obj.log_api_call()
        request.api_token = token_obj
        return func(*args, **kwargs)

    return wrapper


def check_permission(scope_required):
    """Require a scope level based on the token."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = getattr(request, 'api_token', None)
            if not token:
                return args[0]._json_response({
                    'status': 'error',
                    'error_code': 'NO_TOKEN',
                    'message': 'Authentication required'
                }, status=401)

            if scope_required == 'write' and token.scopes not in ['write', 'admin']:
                return args[0]._json_response({
                    'status': 'error',
                    'error_code': 'PERMISSION_DENIED',
                    'message': 'Insufficient permissions'
                }, status=403)

            if scope_required == 'admin' and token.scopes != 'admin':
                return args[0]._json_response({
                    'status': 'error',
                    'error_code': 'ADMIN_REQUIRED',
                    'message': 'Admin access required'
                }, status=403)

            return func(*args, **kwargs)

        return wrapper
    return decorator


class LeadAPIController(http.Controller):
    """Advanced REST API endpoints for Lead Generation."""

    def _json_response(self, payload, status=200):
        # Standard JSON response helper.
        return request.make_response(
            json.dumps(payload),
            headers=[('Content-Type', 'application/json')],
            status=status,
        )

    def _ensure_db(self):
        # Select a database for public API requests.
        if not request.session.db:
            request.session.db = request.params.get('db') or 'odoo'

    def _log_activity(self, lead_id, activity_type, description, field_name=None, old_value=None, new_value=None):
        # Track API actions for auditing.
        try:
            request.env['lead.activity'].sudo().create({
                'lead_id': lead_id,
                'activity_type': activity_type,
                'description': description,
                'field_name': field_name,
                'old_value': old_value,
                'new_value': new_value,
                'user_id': request.api_token.user_id.id if hasattr(request, 'api_token') else None,
                'api_token_id': request.api_token.id if hasattr(request, 'api_token') else None,
            })
        except Exception as exc:
            _logger.warning('Failed to log activity: %s', exc)

    def _trigger_webhook(self, event_type, lead_data):
        # Fire-and-forget webhooks for external integrations.
        try:
            webhooks = request.env['lead.webhook'].sudo().search([
                ('is_active', '=', True),
                ('event_type', 'in', [event_type, 'all'])
            ])

            for webhook in webhooks:
                headers = {'Content-Type': 'application/json'}

                if webhook.secret:
                    signature = hmac.new(
                        webhook.secret.encode(),
                        json.dumps(lead_data).encode(),
                        hashlib.sha256
                    ).hexdigest()
                    headers['X-Webhook-Signature'] = signature

                if webhook.headers:
                    try:
                        headers.update(json.loads(webhook.headers))
                    except Exception:
                        pass

                try:
                    requests.post(
                        webhook.url,
                        json={
                            'event': event_type,
                            'timestamp': fields.Datetime.now().isoformat(),
                            'data': lead_data,
                        },
                        headers=headers,
                        timeout=10
                    )
                except Exception as exc:
                    _logger.warning('Webhook failed: %s', exc)
        except Exception as exc:
            _logger.warning('Error triggering webhooks: %s', exc)

    # =============== AUTHENTICATION ===============
    @http.route('/api/auth/token', auth='public', type='http', methods=['POST'], csrf=False)
    def get_token(self):
        """Generate an API token using email and password."""
        try:
            self._ensure_db()
            data = request.httprequest.get_json(silent=True) or {}

            email = data.get('email')
            password = data.get('password')
            scope = data.get('scope', 'read')

            if not email or not password:
                return self._json_response({
                    'status': 'error',
                    'message': 'Email and password required'
                }, status=400)

            user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
            if not user:
                return self._json_response({
                    'status': 'error',
                    'message': 'Invalid credentials'
                }, status=401)

            try:
                user._check_credentials(password, {'interactive': False})
            except AccessDenied:
                return self._json_response({
                    'status': 'error',
                    'message': 'Invalid credentials'
                }, status=401)

            token_obj = request.env['lead.api.token'].sudo().generate_token(
                name=f'Token for {email}',
                user_id=user.id,
                scope=scope
            )

            return self._json_response({
                'status': 'success',
                'data': {
                    'token': token_obj.token,
                    'expires_at': token_obj.expires_at,
                    'scope': token_obj.scopes,
                }
            }, status=201)

        except Exception as exc:
            _logger.exception('Error generating token')
            return self._json_response({
                'status': 'error',
                'message': str(exc)
            }, status=500)

    # =============== CREATE (POST) ===============
    @http.route('/api/leads', auth='public', type='http', methods=['POST'], csrf=False)
    @token_required
    @check_permission('write')
    def create_lead(self):
        """Create a new lead."""
        try:
            self._ensure_db()
            data = request.httprequest.get_json(silent=True) or {}

            if not data.get('name'):
                return self._json_response({
                    'status': 'error',
                    'error_code': 'MISSING_NAME',
                    'message': 'Lead name is required'
                }, status=400)

            if not data.get('email'):
                return self._json_response({
                    'status': 'error',
                    'error_code': 'MISSING_EMAIL',
                    'message': 'Email is required'
                }, status=400)

            existing = request.env['lead.generation'].sudo().search([
                ('email', '=', data.get('email'))
            ], limit=1)
            if existing:
                return self._json_response({
                    'status': 'error',
                    'error_code': 'DUPLICATE_EMAIL',
                    'message': 'Lead with this email already exists'
                }, status=409)

            create_vals = {
                'name': data.get('name'),
                'email': data.get('email'),
                'phone': data.get('phone', ''),
                'company': data.get('company', ''),
                'lead_source': data.get('lead_source', 'website'),
                'status': 'new',
                'budget': data.get('budget', 0),
                'expected_closing_date': data.get('expected_closing_date'),
                'notes': data.get('notes', ''),
            }

            if data.get('assigned_user_id'):
                create_vals['user_id'] = data.get('assigned_user_id')

            lead = request.env['lead.generation'].sudo().create(create_vals)

            self._log_activity(lead.id, 'created', 'Lead created via API')

            lead_data = {
                'id': lead.id,
                'name': lead.name,
                'email': lead.email,
                'status': lead.status,
                'created_date': lead.create_date.isoformat() if lead.create_date else None,
            }

            self._trigger_webhook('lead_created', lead_data)

            return self._json_response({
                'status': 'success',
                'data': lead_data,
                'message': 'Lead created successfully'
            }, status=201)

        except Exception as exc:
            _logger.exception('Error creating lead')
            return self._json_response({
                'status': 'error',
                'error_code': 'SERVER_ERROR',
                'message': str(exc)
            }, status=500)

    # =============== READ - GET ALL (GET) ===============
    @http.route('/api/leads', auth='public', type='http', methods=['GET'], csrf=False)
    @token_required
    def get_all_leads(self):
        """Get leads with filtering and pagination."""
        try:
            self._ensure_db()
            params = request.httprequest.args

            page = int(params.get('page', 1))
            limit = min(int(params.get('limit', 10)), 100)

            domain = [('active', '=', True)]

            if params.get('status'):
                domain.append(('status', '=', params.get('status')))
            if params.get('lead_source'):
                domain.append(('lead_source', '=', params.get('lead_source')))
            if params.get('search'):
                domain.append(('|',
                    ('name', 'ilike', params.get('search')),
                    ('email', 'ilike', params.get('search'))
                ))
            if params.get('assigned_user_id'):
                domain.append(('user_id', '=', int(params.get('assigned_user_id'))))
            if params.get('budget_min'):
                domain.append(('budget', '>=', float(params.get('budget_min'))))
            if params.get('budget_max'):
                domain.append(('budget', '<=', float(params.get('budget_max'))))
            if params.get('created_after'):
                domain.append(('create_date', '>=', params.get('created_after')))
            if params.get('created_before'):
                domain.append(('create_date', '<=', params.get('created_before')))

            total_count = request.env['lead.generation'].sudo().search_count(domain)

            offset = (page - 1) * limit
            leads = request.env['lead.generation'].sudo().search(
                domain,
                offset=offset,
                limit=limit,
                order='create_date desc'
            )

            leads_data = []
            for lead in leads:
                leads_data.append({
                    'id': lead.id,
                    'name': lead.name,
                    'email': lead.email,
                    'phone': lead.phone,
                    'company': lead.company,
                    'status': lead.status,
                    'lead_source': lead.lead_source,
                    'budget': lead.budget,
                    'created_date': lead.create_date.isoformat() if lead.create_date else None,
                })

            return self._json_response({
                'status': 'success',
                'data': leads_data,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total_count': total_count,
                    'total_pages': (total_count + limit - 1) // limit,
                },
                'filters_applied': {
                    'status': params.get('status'),
                    'lead_source': params.get('lead_source'),
                    'search': params.get('search'),
                },
                'message': f'Retrieved {len(leads)} leads'
            }, status=200)

        except Exception as exc:
            _logger.exception('Error fetching leads')
            return self._json_response({
                'status': 'error',
                'error_code': 'SERVER_ERROR',
                'message': str(exc)
            }, status=500)

    # =============== READ - GET ONE (GET) ===============
    @http.route('/api/leads/<int:lead_id>', auth='public', type='http', methods=['GET'], csrf=False)
    @token_required
    def get_lead(self, lead_id):
        """Get a lead with activity history."""
        try:
            self._ensure_db()
            lead = request.env['lead.generation'].sudo().browse(lead_id)

            if not lead.exists():
                return self._json_response({
                    'status': 'error',
                    'error_code': 'NOT_FOUND',
                    'message': f'Lead with ID {lead_id} not found'
                }, status=404)

            activities = request.env['lead.activity'].sudo().search([
                ('lead_id', '=', lead_id)
            ], limit=10, order='create_date desc')

            activity_data = []
            for activity in activities:
                activity_data.append({
                    'type': activity.activity_type,
                    'description': activity.description,
                    'timestamp': activity.create_date.isoformat() if activity.create_date else None,
                    'user': activity.user_id.name if activity.user_id else 'API',
                })

            return self._json_response({
                'status': 'success',
                'data': {
                    'id': lead.id,
                    'name': lead.name,
                    'email': lead.email,
                    'phone': lead.phone,
                    'company': lead.company,
                    'status': lead.status,
                    'lead_source': lead.lead_source,
                    'budget': lead.budget,
                    'notes': lead.notes,
                    'created_date': lead.create_date.isoformat() if lead.create_date else None,
                    'activity_history': activity_data,
                },
                'message': 'Lead retrieved successfully'
            }, status=200)

        except Exception as exc:
            _logger.exception('Error fetching lead')
            return self._json_response({
                'status': 'error',
                'error_code': 'SERVER_ERROR',
                'message': str(exc)
            }, status=500)

    # =============== UPDATE (PUT) ===============
    @http.route('/api/leads/<int:lead_id>', auth='public', type='http', methods=['PUT'], csrf=False)
    @token_required
    @check_permission('write')
    def update_lead(self, lead_id):
        """Update a lead with activity tracking."""
        try:
            self._ensure_db()
            lead = request.env['lead.generation'].sudo().browse(lead_id)

            if not lead.exists():
                return self._json_response({
                    'status': 'error',
                    'error_code': 'NOT_FOUND',
                    'message': f'Lead with ID {lead_id} not found'
                }, status=404)

            data = request.httprequest.get_json(silent=True) or {}

            allowed_fields = [
                'name', 'email', 'phone', 'company', 'status',
                'lead_source', 'budget', 'expected_closing_date', 'notes', 'user_id'
            ]

            update_data = {}
            for field in allowed_fields:
                if field in data:
                    update_data[field] = data[field]

            if not update_data:
                return self._json_response({
                    'status': 'error',
                    'error_code': 'NO_DATA',
                    'message': 'No valid fields to update'
                }, status=400)

            changes = {}
            for field, value in update_data.items():
                old_value = getattr(lead, field, '')
                if old_value != value:
                    changes[field] = {
                        'old': str(old_value),
                        'new': str(value),
                    }

            lead.write(update_data)

            for field, change in changes.items():
                self._log_activity(
                    lead.id,
                    'updated',
                    f'Field {field} changed',
                    field_name=field,
                    old_value=change['old'],
                    new_value=change['new']
                )

            self._trigger_webhook('lead_updated', {
                'id': lead.id,
                'changes': changes,
            })

            return self._json_response({
                'status': 'success',
                'data': {
                    'id': lead.id,
                    'name': lead.name,
                    'status': lead.status,
                },
                'changes': changes,
                'message': 'Lead updated successfully'
            }, status=200)

        except Exception as exc:
            _logger.exception('Error updating lead')
            return self._json_response({
                'status': 'error',
                'error_code': 'SERVER_ERROR',
                'message': str(exc)
            }, status=500)

    # =============== DELETE (DELETE) ===============
    @http.route('/api/leads/<int:lead_id>', auth='public', type='http', methods=['DELETE'], csrf=False)
    @token_required
    @check_permission('admin')
    def delete_lead(self, lead_id):
        """Archive a lead (soft delete)."""
        try:
            self._ensure_db()
            lead = request.env['lead.generation'].sudo().browse(lead_id)

            if not lead.exists():
                return self._json_response({
                    'status': 'error',
                    'error_code': 'NOT_FOUND',
                    'message': f'Lead with ID {lead_id} not found'
                }, status=404)

            lead.write({'active': False})

            self._log_activity(lead.id, 'deleted', 'Lead archived via API')

            self._trigger_webhook('lead_deleted', {
                'id': lead.id,
                'name': lead.name,
            })

            return self._json_response({
                'status': 'success',
                'message': f'Lead {lead_id} deleted successfully'
            }, status=200)

        except Exception as exc:
            _logger.exception('Error deleting lead')
            return self._json_response({
                'status': 'error',
                'error_code': 'SERVER_ERROR',
                'message': str(exc)
            }, status=500)

    # =============== BULK OPERATIONS ===============
    @http.route('/api/leads/bulk/update', auth='public', type='http', methods=['PUT'], csrf=False)
    @token_required
    @check_permission('write')
    def bulk_update_leads(self):
        """Bulk update multiple leads."""
        try:
            self._ensure_db()
            data = request.httprequest.get_json(silent=True) or {}

            lead_ids = data.get('lead_ids', [])
            if not lead_ids:
                return self._json_response({
                    'status': 'error',
                    'message': 'lead_ids required'
                }, status=400)

            leads = request.env['lead.generation'].sudo().browse(lead_ids)
            update_data = {k: v for k, v in data.items() if k != 'lead_ids'}
            leads.write(update_data)

            return self._json_response({
                'status': 'success',
                'data': {
                    'updated_count': len(leads),
                },
                'message': f'Updated {len(leads)} leads'
            }, status=200)

        except Exception as exc:
            _logger.exception('Error in bulk update')
            return self._json_response({
                'status': 'error',
                'message': str(exc)
            }, status=500)

    # =============== ANALYTICS ===============
    @http.route('/api/leads/analytics', auth='public', type='http', methods=['GET'], csrf=False)
    @token_required
    def get_analytics(self):
        """Return lead statistics and activity totals."""
        try:
            self._ensure_db()

            total_leads = request.env['lead.generation'].sudo().search_count([
                ('active', '=', True)
            ])

            status_count = {}
            statuses = ['new', 'contacted', 'qualified', 'proposal_sent', 'negotiation', 'won', 'lost']
            for status in statuses:
                status_count[status] = request.env['lead.generation'].sudo().search_count([
                    ('status', '=', status),
                    ('active', '=', True)
                ])

            source_count = {}
            sources = ['website', 'phone', 'email', 'social_media', 'referral', 'walk_in', 'other']
            for source in sources:
                source_count[source] = request.env['lead.generation'].sudo().search_count([
                    ('lead_source', '=', source),
                    ('active', '=', True)
                ])

            leads = request.env['lead.generation'].sudo().search([
                ('active', '=', True)
            ])
            avg_budget = sum(lead.budget for lead in leads) / len(leads) if leads else 0

            created_today = request.env['lead.generation'].sudo().search_count([
                ('create_date', '>=', f'{date.today()} 00:00:00'),
                ('active', '=', True)
            ])

            conversion_rate = 0
            if total_leads:
                conversion_rate = (status_count.get('won', 0) / total_leads) * 100

            return self._json_response({
                'status': 'success',
                'data': {
                    'total_leads': total_leads,
                    'leads_by_status': status_count,
                    'leads_by_source': source_count,
                    'average_budget': avg_budget,
                    'created_today': created_today,
                    'conversion_rate': f'{conversion_rate:.2f}%'
                },
                'message': 'Analytics retrieved successfully'
            }, status=200)

        except Exception as exc:
            _logger.exception('Error fetching analytics')
            return self._json_response({
                'status': 'error',
                'message': str(exc)
            }, status=500)
