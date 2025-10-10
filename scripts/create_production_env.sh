#!/usr/bin/env bash
#
# Script to create .env.production file with secure defaults
# Usage: ./scripts/create_production_env.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env.production"

# Helper functions
generate_secret() { python3 -c "import secrets; print(secrets.token_urlsafe(50))"; }
prompt() { local p="$1" d="$2"; read -p "$p${d:+ [$d]}: " v; echo "${v:-$d}"; }
prompt_secret() { local p="$1"; read -s -p "$p: " v; echo "" >&2; echo "$v"; }
prompt_yn() { local p="$1" d="${2:-False}"; local def=$([ "$d" = "True" ] && echo "yes" || echo "no"); read -p "$p (yes/no) [$def]: " v; v="${v:-$def}"; [[ $v =~ ^[Yy] ]] && echo "True" || echo "False"; }

echo "================================================"
echo "  DAISY Production Environment Setup"
echo "================================================"

# Check if file exists and backup
if [ -f "$ENV_FILE" ]; then
    read -p "⚠️  .env.production exists. Overwrite? (yes/no): " -r
    [[ ! $REPLY =~ ^[Yy] ]] && echo "Aborted." && exit 0
    cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✓ Backup created"
fi

echo ""
echo "Press Enter for defaults (shown in brackets)"
echo ""

# Start file
cat > "$ENV_FILE" << EOF
# DAISY Production Configuration - $(date +"%Y-%m-%d %H:%M:%S")
ENVIRONMENT=production
DJANGO_READ_DOTENV=true
DEBUG=False

EOF

# Security
echo "🔐 Security"
SECRET_KEY=$(prompt "SECRET_KEY (empty=generate)" "")
[ -z "$SECRET_KEY" ] && SECRET_KEY=$(generate_secret) && echo "  ✓ Generated"
GLOBAL_API_KEY=$(prompt "GLOBAL_API_KEY (empty=generate)" "")
[ -z "$GLOBAL_API_KEY" ] && GLOBAL_API_KEY=$(generate_secret) && echo "  ✓ Generated"

cat >> "$ENV_FILE" << EOF
SECRET_KEY=$SECRET_KEY
GLOBAL_API_KEY=$GLOBAL_API_KEY

EOF

# Database
echo ""
echo "🗄️  Database"
DB_HOST=$(prompt "Host" "db")
DB_PORT=$(prompt "Port" "5432")
DB_NAME=$(prompt "Name" "daisy")
DB_USER=$(prompt "User" "daisy")
DB_PASS=$(prompt_secret "Password")

cat >> "$ENV_FILE" << EOF
DATABASE_URL=postgres://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}

EOF

# Celery
echo ""
echo "📬 Message Queue"
MQ_HOST=$(prompt "RabbitMQ host" "mq")
MQ_PORT=$(prompt "Port" "5672")
MQ_USER=$(prompt "User" "guest")
MQ_PASS=$(prompt "Password" "guest")

cat >> "$ENV_FILE" << EOF
CELERY_BROKER_URL=amqp://${MQ_USER}:${MQ_PASS}@${MQ_HOST}:${MQ_PORT}//
CELERY_RESULT_BACKEND=django-db

EOF

# Solr
echo ""
echo "🔍 Search Engine"
SOLR_HOST=$(prompt "Solr host" "solr")
SOLR_PORT=$(prompt "Port" "8983")

cat >> "$ENV_FILE" << EOF
SOLR_URL=http://${SOLR_HOST}:${SOLR_PORT}/solr/daisy
SOLR_URL_TEST=http://${SOLR_HOST}:${SOLR_PORT}/solr/daisy_test
SOLR_ADMIN_URL=http://${SOLR_HOST}:${SOLR_PORT}/solr/admin/cores

EOF

# Networking
echo ""
echo "🌐 Networking"
ALLOWED_HOSTS=$(prompt "Allowed hosts (comma-separated)" "example.com")
CSRF_ORIGINS=$(prompt "CSRF origins (with https://)" "https://example.com")

cat >> "$ENV_FILE" << EOF
ALLOWED_HOSTS=$ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS=$CSRF_ORIGINS
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

EOF

# Email
echo ""
echo "� Email (optional)"
EMAIL_HOST=$(prompt "Email host" "localhost")
EMAIL_PORT=$(prompt "Port" "25")

cat >> "$ENV_FILE" << EOF
EMAIL_HOST=$EMAIL_HOST
EMAIL_PORT=$EMAIL_PORT

EOF

# Optional integrations
echo ""
echo "🔌 Optional Integrations"

# REMS
REMS_ENABLED=$(prompt_yn "Enable REMS?")
echo "REMS_INTEGRATION_ENABLED=$REMS_ENABLED" >> "$ENV_FILE"
if [ "$REMS_ENABLED" = "True" ]; then
    cat >> "$ENV_FILE" << EOF
REMS_URL=$(prompt "REMS URL" "")
REMS_API_USER=$(prompt "REMS User" "")
REMS_API_KEY=$(prompt_secret "REMS Key")
REMS_VERIFY_SSL=True
EOF
fi
echo "" >> "$ENV_FILE"

# LDAP
LDAP_ENABLED=$(prompt_yn "Enable LDAP?")
echo "LDAP_ENABLED=$LDAP_ENABLED" >> "$ENV_FILE"
if [ "$LDAP_ENABLED" = "True" ]; then
    cat >> "$ENV_FILE" << EOF
AUTH_LDAP_SERVER_URI=$(prompt "AUTH_LDAP_SERVER_URI" "ldap://localhost/")
AUTH_LDAP_BIND_DN=$(prompt "AUTH_LDAP_BIND_DN" "")
AUTH_LDAP_BIND_PASSWORD=$(prompt_secret "AUTH_LDAP_BIND_PASSWORD")
EOF
fi
echo "" >> "$ENV_FILE"

# Keycloak
KC_ENABLED=$(prompt_yn "Enable Keycloak?")
echo "KEYCLOAK_INTEGRATION=$KC_ENABLED" >> "$ENV_FILE"
if [ "$KC_ENABLED" = "True" ]; then
    KC_REALM=$(prompt "KC Realm" "daisy")
    cat >> "$ENV_FILE" << EOF
KEYCLOAK_URL=$(prompt "KC URL" "https://sso.example.com/")
KEYCLOAK_REALM_LOGIN=$KC_REALM
KEYCLOAK_REALM_ADMIN=$KC_REALM
KEYCLOAK_USER=$(prompt "KC User" "")
KEYCLOAK_PASS=$(prompt_secret "KC Password")
EOF
fi
echo "" >> "$ENV_FILE"

# OIDC
OIDC_ENABLED=$(prompt_yn "Enable OIDC?")
echo "OIDC_ENABLED=$OIDC_ENABLED" >> "$ENV_FILE"
if [ "$OIDC_ENABLED" = "True" ]; then
    cat >> "$ENV_FILE" << EOF
OIDC_CLIENT_ID=$(prompt "OIDC Client ID" "")
OIDC_CLIENT_SECRET=$(prompt_secret "OIDC Client Secret")
OIDC_METADATA_URL=$(prompt "OIDC Metadata URL" "")
EOF
fi
echo "" >> "$ENV_FILE"

# Application settings
cat >> "$ENV_FILE" << 'EOF'
# Optional: Uncomment and customize
# COMPANY=LCSB
# STATIC_ROOT=/static
NOTIFICATIONS_DISABLED=False
# ACCESS_DEFAULT_EXPIRATION_DAYS=90
EOF

# Set permissions
chmod 600 "$ENV_FILE"

echo ""
echo "================================================"
echo "✅ File created: $ENV_FILE"
echo "================================================"
echo ""
echo "⚠️  Security reminders:"
echo "  • Review the file before using"
echo "  • Never commit to version control"
echo "  • File permissions set to 600"
echo ""
echo "Next steps:"
echo "  1. Review: cat $ENV_FILE"
echo "  2. Test: python manage.py check --deploy"
echo ""
