# Integrations

DAISY can be connected to external systems to extend its role beyond internal bookkeeping. These integrations are part of **DS-PACK**, a data management toolkit published by [ELIXIR Luxembourg](https://elixir-luxembourg.org). Full setup instructions are available in the DS-PACK documentation (under development).

## Data Catalog

DAISY can publish dataset metadata to an external data catalog. Once a dataset is exposed to a catalog endpoint, the catalog can display it publicly or within a restricted portal — making datasets discoverable to researchers and collaborators.

The link between DAISY and the catalog is maintained through an *Exposure*: a record that connects a specific dataset to a specific catalog endpoint. If an exposure is no longer valid, it can be deprecated without being deleted, preserving the audit trail.

This integration is particularly useful for making datasets from ongoing projects visible to potential data users before formal access is granted.

## Data Access Requests (REMS)

DAISY integrates with [REMS](https://github.com/CSCfi/rems) (Resource Entitlement Management System), an open-source system for managing data access applications. REMS handles the workflow of a data access request — application form, review, approval — and notifies DAISY of the outcome via a webhook.

In this setup:

- A dataset is *exposed* to a REMS instance, with a specific application form assigned to it.
- Researchers submit access requests through REMS.
- When a request is approved or rejected, REMS calls back to DAISY, which can record the resulting *Access* entry on the dataset automatically.

This removes the need to manually enter approved access grants in DAISY and keeps the access register up to date without extra administrative effort.

---

For deployment and configuration of these integrations, see the DS-PACK documentation (under development) or the [API Reference](api.md).
