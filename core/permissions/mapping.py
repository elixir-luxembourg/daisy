"""
This module defines the groups permissions on the different models.

These permissions are defined at the class level.
If a user does not belong to a group with class-level permissions on the model they
want to access, the permissions have to be handled at the instance level.
"""

from core.constants import Groups, Permissions

ALL_MODELS = (
    "core.Access",
    "core.Cohort",
    "core.Contact",
    "core.Contract",
    "core.DataDeclaration",
    "core.Dataset",
    "core.Document",
    "core.LegalBasis",
    "core.Partner",
    "core.Project",
    "core.Publication",
    "core.Share",
    "core.DataLocation",
)

# Additional permissions that can be granted on entities (django creates VIEW, EDIT, CREATE, DELETE by default)
# We add PROTECTED (can see/edit protected elements) and ADMIN (can grant permissions on an entity)
# ANY MODIFICATION TO THIS DICT NEEDS A DB MIGRATION FOR IT TO WORK
PERMISSION_MAPPING = {
    "Contract": [
        (
            f"{Permissions.PROTECTED.value}_contract",
            "Can edit PROTECTED elements of Contract instances",
        ),
        (
            f"{Permissions.ADMIN.value}_contract",
            "Can edit permissions on Contract instances",
        ),
    ],
    "Dataset": [
        (
            f"{Permissions.PROTECTED.value}_dataset",
            "Can edit PROTECTED elements of Dataset instances",
        ),
        (
            f"{Permissions.ADMIN.value}_dataset",
            "Can edit permissions on Dataset instances",
        ),
    ],
    "Project": [
        (
            f"{Permissions.PROTECTED.value}_project",
            "Can edit PROTECTED elements of Project instances",
        ),
        (
            f"{Permissions.ADMIN.value}_project",
            "Can edit permissions on Dataset instances",
        ),
    ],
}

GROUP_PERMISSIONS = {
    Groups.DATA_STEWARD: {
        model: [
            model.replace(".", f".{perm.value}_").lower()
            for perm in Permissions
            if model.split(".")[1] in PERMISSION_MAPPING
            or perm.value not in ["admin", "protected"]
        ]
        for model in ALL_MODELS
    },
    Groups.AUDITOR: {
        "core.Contract": (f"core.{Permissions.PROTECTED.value}_contract",),
        "core.Dataset": (f"core.{Permissions.PROTECTED.value}_dataset",),
        "core.Project": (f"core.{Permissions.PROTECTED.value}_project",),
    },
    Groups.LEGAL: {
        "core.Contract": (
            f"core.{Permissions.EDIT.value}_contract",
            f"core.{Permissions.PROTECTED.value}_contract",
        )
    },
    Groups.VIP: {},
}
