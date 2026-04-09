# controllers/lead_api.py

import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class LeadAPIController(http.Controller):
    """REST API endpoints for Lead Generation"""

    def _json_response(self, payload, status=200):
        return request.make_response(
            json.dumps(payload),
            headers=[('Content-Type', 'application/json')],
            status=status,
        )
    
    # =============== CREATE (POST) ===============
    @http.route('/api/leads', auth='public', type='http', methods=['POST'], csrf=False)
    def create_lead(self):
        """
        Create a new lead
        
        Example JSON:
        {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "company": "ABC Corp",
            "lead_source": "website",
            "budget": 50000,
            "notes": "Interested in services"
        }
        """
        try:
            data = request.httprequest.get_json(silent=True) or {}
            
            # Validate required fields
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
            
            # Check duplicate email
            existing = request.env['lead.generation'].search([
                ('email', '=', data.get('email'))
            ])
            if existing:
                return self._json_response({
                    'status': 'error',
                    'error_code': 'DUPLICATE_EMAIL',
                    'message': f'Lead with this email already exists'
                }, status=409)
            
            # Create lead
            lead = request.env['lead.generation'].create({
                'name': data.get('name'),
                'email': data.get('email'),
                'phone': data.get('phone', ''),
                'company': data.get('company', ''),
                'lead_source': data.get('lead_source', 'website'),
                'status': 'new',
                'budget': data.get('budget', 0),
                'notes': data.get('notes', ''),
            })
            
            _logger.info(f'Lead created: {lead.id}')
            
            return self._json_response({
                'status': 'success',
                'data': {
                    'id': lead.id,
                    'name': lead.name,
                    'email': lead.email,
                    'status': lead.status,
                },
                'message': 'Lead created successfully'
            }, status=201)
        
        except Exception as e:
            _logger.error(f'Error creating lead: {str(e)}')
            return self._json_response({
                'status': 'error',
                'error_code': 'SERVER_ERROR',
                'message': 'An error occurred'
            }, status=500)
    
    
    # =============== READ - GET ALL (GET) ===============
    @http.route('/api/leads', auth='public', type='http', methods=['GET'], csrf=False)
    def get_all_leads(self):
        """
        Get all leads with filtering and pagination
        
        Query params:
        - page: Page number (default: 1)
        - limit: Records per page (default: 10, max: 100)
        - status: Filter by status
        - lead_source: Filter by source
        - search: Search in name/email
        """
        try:
            params = request.httprequest.args
            page = int(params.get('page', 1))
            limit = min(int(params.get('limit', 10)), 100)
            status = params.get('status')
            lead_source = params.get('lead_source')
            search = params.get('search')
            
            # Build search domain
            domain = [('active', '=', True)]
            
            if status:
                domain.append(('status', '=', status))
            
            if lead_source:
                domain.append(('lead_source', '=', lead_source))
            
            if search:
                domain.append(('|',
                    ('name', 'ilike', search),
                    ('email', 'ilike', search)
                ))
            
            # Count total
            total_count = request.env['lead.generation'].search_count(domain)
            
            # Fetch leads
            offset = (page - 1) * limit
            leads = request.env['lead.generation'].search(
                domain,
                offset=offset,
                limit=limit,
                order='create_date desc'
            )
            
            # Format response
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
                    'created_date': lead.create_date.strftime('%Y-%m-%d %H:%M:%S') if lead.create_date else '',
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
                'message': f'Retrieved {len(leads)} leads'
            }, status=200)
        
        except ValueError:
            return self._json_response({
                'status': 'error',
                'error_code': 'INVALID_PARAMETER',
                'message': 'Invalid page or limit parameter'
            }, status=400)
        
        except Exception as e:
            _logger.error(f'Error fetching leads: {str(e)}')
            return self._json_response({
                'status': 'error',
                'error_code': 'SERVER_ERROR',
                'message': 'An error occurred'
            }, status=500)
    
    
    # =============== READ - GET ONE (GET) ===============
    @http.route('/api/leads/<int:lead_id>', auth='public', type='http', methods=['GET'], csrf=False)
    def get_lead(self, lead_id):
        """Get a specific lead by ID"""
        try:
            lead = request.env['lead.generation'].browse(lead_id)
            
            if not lead.exists():
                return self._json_response({
                    'status': 'error',
                    'error_code': 'NOT_FOUND',
                    'message': f'Lead with ID {lead_id} not found'
                }, status=404)
            
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
                    'expected_closing_date': lead.expected_closing_date,
                    'notes': lead.notes,
                    'created_date': lead.create_date.strftime('%Y-%m-%d %H:%M:%S') if lead.create_date else '',
                },
                'message': 'Lead retrieved successfully'
            }, status=200)
        
        except Exception as e:
            _logger.error(f'Error fetching lead {lead_id}: {str(e)}')
            return self._json_response({
                'status': 'error',
                'error_code': 'SERVER_ERROR',
                'message': 'An error occurred'
            }, status=500)
    
    
    # =============== UPDATE (PUT) ===============
    @http.route('/api/leads/<int:lead_id>', auth='public', type='http', methods=['PUT'], csrf=False)
    def update_lead(self, lead_id):
        """
        Update a lead
        
        Example JSON (update only what you need):
        {
            "status": "contacted",
            "budget": 75000,
            "notes": "Updated notes"
        }
        """
        try:
            lead = request.env['lead.generation'].browse(lead_id)
            
            if not lead.exists():
                return self._json_response({
                    'status': 'error',
                    'error_code': 'NOT_FOUND',
                    'message': f'Lead with ID {lead_id} not found'
                }, status=404)
            
            data = request.httprequest.get_json(silent=True) or {}
            
            # Allowed fields to update
            allowed_fields = [
                'name', 'email', 'phone', 'company', 'status',
                'lead_source', 'budget', 'expected_closing_date', 'notes'
            ]
            
            # Build update data
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
            
            # Update lead
            lead.write(update_data)
            
            _logger.info(f'Lead {lead_id} updated')
            
            return self._json_response({
                'status': 'success',
                'data': {
                    'id': lead.id,
                    'name': lead.name,
                    'status': lead.status,
                },
                'message': 'Lead updated successfully'
            }, status=200)
        
        except Exception as e:
            _logger.error(f'Error updating lead {lead_id}: {str(e)}')
            return self._json_response({
                'status': 'error',
                'error_code': 'SERVER_ERROR',
                'message': 'An error occurred'
            }, status=500)
    
    
    # =============== DELETE (DELETE) ===============
    @http.route('/api/leads/<int:lead_id>', auth='public', type='http', methods=['DELETE'], csrf=False)
    def delete_lead(self, lead_id):
        """Delete/Archive a lead (soft delete)"""
        try:
            lead = request.env['lead.generation'].browse(lead_id)
            
            if not lead.exists():
                return self._json_response({
                    'status': 'error',
                    'error_code': 'NOT_FOUND',
                    'message': f'Lead with ID {lead_id} not found'
                }, status=404)
            
            # Archive instead of delete
            lead.write({'active': False})
            
            _logger.info(f'Lead {lead_id} archived')
            
            return self._json_response({
                'status': 'success',
                'message': f'Lead {lead_id} deleted successfully'
            }, status=200)
        
        except Exception as e:
            _logger.error(f'Error deleting lead {lead_id}: {str(e)}')
            return self._json_response({
                'status': 'error',
                'error_code': 'SERVER_ERROR',
                'message': 'An error occurred'
            }, status=500)