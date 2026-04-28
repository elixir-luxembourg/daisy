---
mount: /manual/access_management
name: "Access Management"
---

<small>
[User guide](daisy.md) &raquo; *Access Management*
</small>

# Access Management

An *Access* record documents that a specific person has been granted access to a dataset. GDPR requires that access to personal data is recorded; Access records are DAISY's mechanism for this accountability obligation.

Each access record ties together:

- a **dataset** — the data being accessed
- a **person** — either an internal DAISY user or an external contact (not both; if both need access, create two separate records)
- optionally, a **project** context — if access is being granted in the scope of a different project than the one owning the dataset
- optionally, specific **storage locations** — to scope the grant to a subset of where the data physically resides, rather than the entire dataset

## Remarks are mandatory

Every access record requires a **Remarks** field explaining why access was given and under what conditions. This field is not optional — DAISY will not save an access record without it. When the status of a record changes (e.g. upon termination), the remarks should be updated to reflect the reason.

## Access Status

Access records follow a lifecycle tracked by a status field:

| Status | Meaning |
|--------|---------|
| **Pre-created** | Record exists but access has not yet been activated |
| **Active** | Access is currently valid and in use |
| **Suspended** | Access has been temporarily put on hold |
| **Terminated** | Access has been revoked and is no longer valid |

Status changes are manual, with one automated exception: when a **Grant expires on** date is set and that date passes, DAISY automatically sets the status to *Terminated* and records "Automatically terminated" in the remarks. This happens as a scheduled task and is reflected in the audit log.

Deleting an access record in DAISY does not physically remove it — it sets the status to *Terminated* instead, preserving the full record for accountability purposes.

## Audit Trail

All changes to access records — creation, status transitions, remarks updates — are captured in an immutable audit log. Data Stewards and Auditors can inspect this history to answer the question: *who had access to this data, and when?*

## Who Can Manage Access

Managing access records requires edit permission on the parent dataset:

- **Data Stewards** can create, edit, and terminate access records on any dataset.
- **VIP users** who are Local Custodian of a dataset can manage its access records.
- **Standard users** cannot create or modify access records.

## Notifications

When an access record is approaching its expiry date, DAISY automatically notifies the local custodians of the dataset so they can decide whether to renew or let the grant expire. The notification horizon is configurable per user — see [Notifications](notifications.md).

## API

DAISY exposes access information via its API for use by external systems such as data portals or analysis platforms.

`GET /api/permissions/<user_oidc_id>` returns the list of datasets for which a given user currently holds active, non-expired access. External systems can call this endpoint to enforce access control without replicating the access registry.

Access records can also be created automatically through the **REMS integration**: when a user's data access application is approved in REMS, DAISY creates the corresponding access record automatically. These records are flagged as auto-generated and include the REMS application ID for traceability.
