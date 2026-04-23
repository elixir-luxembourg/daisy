---
mount: manual/users_group
name: "What are the users groups?"
---


# What are the users groups?

DAISY provides several types of user accounts, each with a different set of permissions. All users can view DAISY records; what differs is whether they can edit, delete, access protected elements, and manage other users' access.

## Standard user

The default group for all DAISY users. Standard users can view any *Project*, *Dataset*, *Contract*, or *Definition*, and can create new records of any type. They can edit and delete records they created or where they are assigned as *Local Custodian*. They **cannot** access protected elements (e.g. document attachments) or manage permissions on any record.

## VIP user

Assigned to research principal investigators. VIP users have all the same access as Standard users, and additionally — on records where they are *Local Custodian* — can access protected elements and manage other users' permissions (i.e. they act as administrator for those records).

## Data Steward

Assigned to IT and data management specialists. Data Stewards have elevated privileges across the entire system: they can view, create, edit, and delete any record, access all protected elements, manage permissions on any record, and publish datasets.

## Legal user

Assigned to legal support staff. Legal users can view all records in DAISY. For *Contract* records specifically, they can add, edit, delete, access protected elements, and manage other users' access.

## Auditor

Assigned to external persons given temporary read access, typically during an audit. Auditors can view all records and access protected elements (e.g. document attachments) on *Projects*, *Datasets*, and *Contracts*, but cannot create, edit, delete, or manage permissions.

---

**Note on Local Custodian:** Being assigned as *Local Custodian* on a record (Project, Dataset, Contract, or DAC) extends a user's permissions on that specific record. For Standard users it grants edit and delete access; for VIP users it additionally grants access to protected elements and the ability to manage permissions.

For the full permission breakdown including inheritance rules, see [Users Groups and Permissions](user_management_details.md).
