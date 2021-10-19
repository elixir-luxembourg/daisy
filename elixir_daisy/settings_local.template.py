# Authentication backend
# https://django-guardian.readthedocs.io/en/stable/configuration.html

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]

COMPANY = 'LCSB'  # Used for generating some models' verbose names

HELPDESK_EMAIL = 'lcsb-sysadmins@uni.lu'

# Uncomment the following lines if LDAP authentication will be used and user definitions will be bulk imported from LDAP
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
