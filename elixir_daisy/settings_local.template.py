from celery.schedules import crontab

# SECURITY WARNING: change the key used in production and keep it secret !
GLOBAL_API_KEY = None  # Generate a global api key by e.g. django.core.management.utils.get_random_secret_key()
if GLOBAL_API_KEY is None:
    raise NotImplementedError("You must specify GLOBAL_API_KEY in settings_local.py")

# Authentication backend
# https://django-guardian.readthedocs.io/en/stable/configuration.html

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]


# SECURITY WARNING: change the secret key used in production and keep it secret !
SECRET_KEY = None  # Generate a secret key by e.g. django.core.management.utils.get_random_secret_key()
if SECRET_KEY is None:
    raise NotImplementedError("You must specify SECRET_KEY in settings_local.py")


COMPANY = "LCSB"  # Used for generating some models' verbose names

HELPDESK_EMAIL = "lcsb-sysadmins@uni.lu"
DATASTEWARD_MAILING_LIST = ""  # used when there are notifications errors

# Placeholders on login page
# LOGIN_USERNAME_PLACEHOLDER = ''
# LOGIN_PASSWORD_PLACEHOLDER = ''

# Optional username suffixes
# Setting this variable allows the user to login with a prefix only. Suffix is concatenated to create full user name)
# LOGIN_USERNAME_SUFFIX = ''
# This variable will be stripped from an entered user name and replaced by LOGIN_USERNAME_SUFFIX to create full user name
# LOGIN_USERNAME_ALTERNATIVE_SUFFIX = ''

# Uncomment the following lines if LDAP authentication will be used and user definitions will be bulk imported from LDAP
# import ldap
# from django_auth_ldap.config import LDAPSearch, LDAPSearchUnion
# AUTHENTICATION_BACKENDS = ['django_auth_ldap.backend.LDAPBackend'] + AUTHENTICATION_BACKENDS
# AUTH_LDAP_SERVER_URI = 'ldap://XXXXXXX:389'
# AUTH_LDAP_BIND_DN = ""
# AUTH_LDAP_BIND_PASSWORD = ""  #
# AUTH_LDAP_USER_SEARCH = LDAPSearch("OU=XXXXXX,OU=XXXXXXX,DC=XXXX,DC=XXXX",
#                                   ldap.SCOPE_SUBTREE, "(userPrincipalName=%(user)s)")
# AUTH_LDAP_USER_ATTR_MAP = {"first_name": "givenName", "last_name": "sn", "email": "mail"}


# used as a filter to find users
# LDAP_USERS_IMPORT_CLASS = '(objectClass=person)'
# AD attribute holding the username
# LDAP_USERS_IMPORT_USERNAME_ATTR = 'userprincipalname'
# all records matching LDAP_USERS_IMPORT_CLASS under this dn will be imported
# LDAP_USERS_IMPORT_SEARCH_DN = "OU=XXXXXX,OU=XXXXXX,OU=XXXXXX,DC=uni,DC=XXXXXX"


# list of usernames of users that will imported and set as pi when
# import_users is used to bulk create users from an LDAP server
PREDEFINED_PIS_LIST = [
    # "name.surname@uni.lu", "othername.othersurname@uni.lu",
]

# REMS Integration
REMS_INTEGRATION_ENABLED = False
REMS_ALLOWED_IP_ADDRESSES = []
REMS_SKIP_IP_CHECK = False
ACCESS_DEFAULT_EXPIRATION_DAYS = 90
REMS_API_KEY = ""
REMS_URL = ""
REMS_API_USER = ""
REMS_VERIFY_SSL = True

# IDSERVICE_FUNCTION = 'core.lcsb.idservice.generate_identifier'
IDSERVICE_ENDPOINT = "https://10.240.16.199:8080/v1/api/id"

# Keycloak integration, uncomment and fill the values below
# KEYCLOAK_URL = 'https://root-address-to-your-keycloak.com:443'
# KEYCLOAK_REALM = 'master'
# KEYCLOAK_USER = 'your service user for daisy'
# KEYCLOAK_PASS = 'the password for the service user'

# Celery beat setting to schedule tasks on docker creation
CELERY_BEAT_SCHEDULE = {
    "clean-accesses-every-day": {
        "task": "core.tasks.check_accesses_expiration",
        "schedule": crontab(minute=0, hour=0),  # Execute task at midnight
    }
}
