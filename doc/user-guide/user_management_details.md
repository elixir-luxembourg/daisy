---
mount: manual/user_management_details
name: "Users Groups and Permissions"
---


# Users Groups and Permissions

Access control in DAISY works at two levels.

**User groups** are system-wide roles assigned to a user once. They determine what the user can do across the entire DAISY instance — for example, whether they can edit contracts, access protected documents, or only view records.

**Record-level roles** are assigned on individual records (Projects, Datasets, Contracts, DACs). They grant a user elevated permissions on that specific record, independently of their group. Currently the only record-level role is *Local Custodian*, but additional roles may be introduced in future versions.

These two mechanisms work together: the user group sets a baseline, and record-level roles extend permissions where needed on specific records.

## User Groups

### Standard

The default group assigned to all users. Standard users can:

- View any *Project*, *Dataset*, *Contract*, and *Definition* (*Cohorts*, *Partners*, *Contacts*).
- Create new records of any type.
- Edit and delete records they created.
- Edit and delete records where they are assigned as *Local Custodian*.

Standard users **cannot** access protected elements (e.g. document attachments) or manage permissions on any record, even records they own.

### VIP

Assigned to research principal investigators. VIP users have all the same base access as Standard users, plus:

- Access to protected elements (e.g. document attachments) on records where they are *Local Custodian*.
- Ability to grant and revoke permissions on records where they are *Local Custodian* (they act as administrator for those records).

### Data Steward

Assigned to IT and data management specialists. Data Stewards have system-wide elevated privileges:

- Full permissions (view, create, edit, delete) on all records in the system.
- Access to protected elements on all records.
- Ability to manage permissions on all records.
- Ability to publish datasets and edit controlled-vocabulary metadata.

### Legal

Assigned to legal support staff. Legal users can:

- View all records in DAISY.
- Add, edit, and delete *Contract* records.
- Access protected elements on *Contract* records.
- Grant and revoke permissions on *Contract* records.

### Auditor

Assigned to external persons given temporary read access during an audit. Auditors can:

- View all records in DAISY.
- Access protected elements (e.g. document attachments) on *Projects*, *Datasets*, and *Contracts*.

Auditors **cannot** create, edit, delete, or manage permissions on any record.

### Superuser

The back-end administrator account. Superusers have unrestricted access to all DAISY records and application settings. This account is managed directly by the system administrator.

---
## Record-level roles

### Local Custodian Role

*Local Custodian* is a role that can be assigned on a *Project*, *Dataset*, *Contract*, or *DAC* record. It grants instance-level permissions to the assigned user. The effective permissions depend on the user's group:

| User Group | Local Custodian effect |
|-----------|------------------------|
| **Standard** | Gains **edit** and **delete** on that record. |
| **VIP** | Gains **edit**, **delete**, **protected**, and **admin** on that record. |
| **Data Steward** | Already has all permissions globally; no change. |
| **Legal** | Already has full access to contracts; for Projects/Datasets, gains edit and delete. |

---

## Permissions

Permissions are managed on the following primary objects:

| Object | Protected & Admin permissions |
|--------|-------------------------------|
| **Project** | Yes |
| **Dataset** | Yes |
| **Contract** | Yes |
| **DAC** (Data Access Committee) | Yes |

Other record types (*DataDeclaration*, *LegalBasis*, *Share*, *DataLocation*, *Document*, *Access*) inherit their permissions from their parent object rather than having independently managed permissions.

---

### Permission Inheritance

DAISY uses permission inheritance so that access granted on a parent record automatically extends to its child records. The inheritance chain is:

```
Project
├── Dataset  (inherits from its Project)
│   ├── DataDeclaration
│   ├── LegalBasis
│   ├── Share
│   ├── DataLocation
│   └── Access
└── Contract  (inherits from its Project)
    └── DAC  (inherits from its Contract)

Document  (inherits from its attached Project, Dataset, or Contract)
```

**How it works in practice:**

- If a user has **edit** permission on a *Project*, they also have **edit** permission on all *Datasets* and *Contracts* belonging to that project — even without an explicit grant on the dataset or contract.
- If a user has **edit** on a *Contract*, they also have **edit** on any *DAC* linked to that contract.
- If a user has **protected** on a *Dataset*, they can access *Documents* attached to that dataset.
- Sub-entities (*DataDeclaration*, *LegalBasis*, etc.) always follow the permission of their parent *Dataset*.

Instance-level permissions granted directly on a record always take precedence; the parent cascade only applies when no direct grant exists.

---

### Summary Table

| Group | View all records | Edit | Delete | Protected elements | Admin (grant permissions) |
|-------|:---:|:---:|:---:|:---:|:---:|
| **Superuser** | All | All | All | All | All |
| **Data Steward** | All | All | All | All | All |
| **VIP** (as Local Custodian) | All | Own records | Own records | Own records | Own records |
| **Standard** (as Local Custodian) | All | Own records | Own records | — | — |
| **Legal** | All | Contracts | Contracts | Contracts | Contracts |
| **Auditor** | All | — | — | All | — |

*"Own records" means records where the user is assigned as Local Custodian or is the creator.*

---

## Permission Types

Beyond the standard view/add permissions, DAISY defines four additional permission types:

| Permission | Description |
|-----------|-------------|
| **Edit** | Can modify the properties of a record. |
| **Delete** | Can delete a record. |
| **Protected** | Can view and edit protected elements of a record (e.g. document attachments, sensitive fields). |
| **Admin** | Can grant and revoke permissions on a record for other users. |

These permissions apply at two levels:

- **Group level (global):** Granted to all members of a user group across all records (e.g. Data Stewards have edit permissions everywhere).
- **Instance level:** Granted to specific users on a specific record (e.g. a VIP user who is Local Custodian of a particular project).
