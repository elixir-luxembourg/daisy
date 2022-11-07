"""
This module defines the groups permissions on the different models.

These permissions are defined at the class level.
If a user does not belong to a group with class-level permissions on the model they
want to access, the permissions have to be handled at the instance level.
"""

from core.constants import Permissions, Groups

ALL_PERMS = (Permissions.ADMIN , Permissions.EDIT, Permissions.DELETE, Permissions.VIEW, Permissions.PROTECTED)
ALL_MODELS = ('core.Access', 'core.Cohort', 'core.Contact', 'core.Contract', 'core.DataDeclaration',
              'core.Dataset', 'core.Document', 'core.LegalBasis', 'core.Partner',
              'core.Project', 'core.Publication', 'core.Share', 'core.DataLocation')

# Additional permissions that can be granted on entities (django creates VIEW, EDIT, CREATE, DELETE by default)
# We add PROTECTED (can see/edit protected elements) and ADMIN (can grant permissions on an entity)
PERMISSION_MAPPING = {
    "Contract": ['protected_contract', 'admin_contract'],
    "Dataset": ['protected_dataset', 'admin_dataset'],
    "Project": ['protected_project', 'admin_project'],
}

# PERMISSION_MAPPING = {
#     Groups.DATA_STEWARD: {
#         model: ALL_PERMS for model in ALL_MODELS
#     },
#
#     Groups.AUDITOR:  {
#         model: (Permissions.VIEW, Permissions.PROTECTED) for model in ALL_MODELS
#     },
#     Groups.LEGAL:  {
#         'core.Contract': (Permissions.VIEW, Permissions.EDIT, Permissions.PROTECTED),
#         'core.Document': (Permissions.VIEW, Permissions.EDIT, Permissions.PROTECTED)
#     },
#     Groups.VIP: {}
# }
