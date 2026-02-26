# Daisy API Documentation

## Authentication

Pass API key via header (preferred) or parameter:
- **Header**: `X-API-Key: your_api_key`
- **Parameter**: `?API_KEY=your_api_key_here` (old)

**API Key Types:**
- **Global** - `GLOBAL_API_KEY` env variable (see [administration.md](administration.md))
  - Full access to all endpoints (read/write)
  - Can access unpublished data
- **User** - Personal API key (Django Admin → Users)
  - Read-only (GET requests only)
  - **Permission-based filtering**: Returns only resources where the user has the `protected` permission
  - Applies to datasets, projects, and contracts endpoints
- **Endpoint** - For data catalogs (Django Admin → Endpoints, requires 64-char key)
  - Read-only (GET requests only)

## Endpoints

#### GET `/api/cohorts`
Returns published cohorts.

#### GET `/api/partners`
Returns published partners.
With `API_KEY` returns all partners and can take optional parameters:
- `published` - Filter by status (`true` returns only published and `false` - only unpublished)
- `fields` - Comma-separated field list (`external_id`, `acronym`, `name`)

#### GET `/api/projects`
Export projects in JSON format.
- `project_id` - Filter by project ID
- `fields` - Comma-separated list to filter returned fields (e.g., `name,acronym,start_date`)
  - Available fields: `source`, `id_at_source`, `acronym`, `external_id`, `name` (the project title), `description`, `has_institutional_ethics_approval` (contains has_erp), `has_national_ethics_approval` (contains has_cner), `institutional_ethics_approval_notes`, `national_ethics_approval_notes`, `start_date`, `end_date`, `contacts` (local custodians appear here with `role: "Principal_Investigator"`), `publications`, `metadata`

#### GET `/api/termsearch/<category>`
Search terms by category (`disease`, `phenotype`, `study`, `gene`).
- `search` - Search term (required)
- `page` - Page number (required)

#### GET `/api/users`
Returns list of users (requires login).

#### GET `/api/datasets`
Export datasets in JSON format.
- `project_id` - Filter by project ID
- `project_title` - Filter by exact project title

#### GET `/api/contracts`
Export contracts whose projects have datasets with exposures.
- `project_id` - Filter by project ID

#### GET `/api/permissions/<user_oidc_id>`
Get access permissions for a user by OIDC ID.

### Integration Endpoints

#### POST `/api/rems`
REMS webhook endpoint (IP whitelisting required). **POST only.**
- Requires `REMS_INTEGRATION_ENABLED=true`
- IP must be in `REMS_ALLOWED_IP_ADDRESSES`

#### POST `/api/keycloak/force`
Force Keycloak user synchronization. **POST only.** Requires the global API key.

## Error Responses

```json
{
  "status": "Error",
  "description": "Error message",
  "more": {...}
}
```

Status codes: `200` (Success), `400` (Bad Request), `403` (Forbidden), `404` (Not Found), `405` (Method Not Allowed), `500` (Server Error)

## Examples

```bash
# Export datasets for a project
curl "https://your-instance/api/datasets?API_KEY=key&project_id=42"

# Search disease terms
curl "https://your-instance/api/termsearch/disease?search=cancer&page=1"

# Get projects with specific fields
curl "https://your-instance/api/projects?API_KEY=key&fields=name,acronym"
```
