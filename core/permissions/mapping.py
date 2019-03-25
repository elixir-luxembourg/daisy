from core.constants import Permissions, Groups

ALL_PERMS = (Permissions.ADMIN , Permissions.EDIT, Permissions.DELETE, Permissions.VIEW, Permissions.PROTECTED)


PERMISSION_MAPPING = {
    Groups.DATA_STEWARD: {
        'core.Project': ALL_PERMS,
    },
    Groups.AUDITOR:  {
        'core.Project': (Permissions.VIEW, Permissions.PROTECTED),

    },
    Groups.LEGAL:  {
        'core.Project': (Permissions.VIEW, Permissions.PROTECTED),
    },
    Groups.VIP: {}
}
