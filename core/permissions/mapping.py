"""
This module defines the groups permissions on the different models.

These permissions are defined at the class level.
If a user does not belong to a group with class-level permissions on the model they
want to access, the permissions have to be handled at the instance level.
"""

from core.constants import Groups

ALL_MODELS = ('core.Access', 'core.Cohort', 'core.Contact', 'core.Contract', 'core.DataDeclaration',
              'core.Dataset', 'core.Document', 'core.LegalBasis', 'core.Partner',
              'core.Project', 'core.Publication', 'core.Share', 'core.DataLocation')

ALL_PERMISSIONS = ('add', 'admin', 'change', 'delete', 'protected', 'view')

# Additional permissions that can be granted on entities (django creates VIEW, EDIT, CREATE, DELETE by default)
# We add PROTECTED (can see/edit protected elements) and ADMIN (can grant permissions on an entity)
PERMISSION_MAPPING = {
    "Contract": [
        ('protected_contract', 'Can edit PROTECTED elements of Contract instances'),
        ('admin_contract', 'Can edit permissions on Contract instances'),
    ],
    "Dataset": [
        ('protected_dataset', 'Can edit PROTECTED elements of Dataset instances'),
        ('admin_dataset', 'Can edit permissions on Dataset instances'),
    ],
    "Project": [
        ('protected_project', 'Can edit PROTECTED elements of Project instances'),
        ('admin_project', 'Can edit permissions on Dataset instances'),
    ],
}

GROUP_PERMISSIONS = {
    Groups.DATA_STEWARD: {
        model: [
            model.replace('.', f'.{perm}_')
            for perm in ALL_PERMISSIONS
            if model.split('.')[1] in PERMISSION_MAPPING
               or perm not in ['admin', 'protected']
        ] for model in ALL_MODELS
    },
    Groups.AUDITOR: {
        'core.Contract': ('core.protected_contract',),
        'core.Dataset': ('core.protected_dataset',),
        'core.Project': ('core.protected_project',),
    },
    Groups.LEGAL: {
        'core.Contract': ('core.change_contract', 'core.protected_contract', 'core.delete_contract')
    }
}