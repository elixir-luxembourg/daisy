---
mount: /manual/exposure_management
name: "Dataset Publishing and Exposures"
---

<small>
[User guide](daisy.md) &raquo; *Dataset Publishing and Exposures*
</small>

# Dataset Publishing and Exposures

Publishing a dataset makes it discoverable outside DAISY — in an external data catalog, or through a data access request system such as REMS. Publishing is controlled and auditable: it requires a Data Steward, generates a permanent identifier for the dataset, and produces an *Exposure* record that can be deprecated but never silently removed.

## Endpoints

An *Endpoint* represents an external system that datasets can be published to. Endpoints are configured by a system administrator and are not editable by regular users. Each endpoint has:

- a **name** identifying the target system (e.g. a data catalog or a REMS instance)
- a **URL pattern** that resolves to the dataset's public page, using `${entity_id}` as a placeholder for the dataset's accession number
- an **API key** used to authenticate calls from the external system back to DAISY

Endpoints are set up once and then available to Data Stewards when creating exposures.

## Exposures

An *Exposure* is the record that connects a specific dataset to a specific endpoint. Creating an exposure is what makes a dataset "published". Each exposure records:

- which **endpoint** the dataset is exposed to
- the **REMS form** assigned for access requests (form ID and name, populated from REMS)
- who created the exposure and when
- whether to attach access requests as PDF to REMS remarks

!!! warning
    Only one active exposure can exist per dataset–endpoint combination. If a dataset needs to be re-exposed to the same endpoint (e.g. after a form change), the existing exposure must first be deprecated.

!!! info "Who can manage exposures"
    Only **Data Stewards** can create, edit, or deprecate exposures.

## Publication Status

A dataset's publication status is derived from its exposures:

| Status | Condition |
|--------|-----------|
| **Unpublished** | No exposures exist for this dataset |
| **Published** | At least one active (non-deprecated) exposure exists |
| **Deprecated** | Exposures exist but all are deprecated |

The status is visible on the dataset detail page and is used by the API to control which datasets are returned to external consumers.

## ELU Accession Number

When a dataset is published for the first time — i.e. when its first exposure is created — DAISY automatically generates a permanent **ELU accession number** in the format `ELU_I_XXX`. This identifier:

- is used as the `${entity_id}` in the endpoint's URL pattern, forming the dataset's public URL in the external catalog
- is used by the DAISY API to identify datasets in responses to external systems
- cannot be changed after it is assigned

!!! warning
    The ELU accession number is permanent. Once assigned it cannot be changed, even if the dataset is later deprecated or re-published.

The accession number is also what links an approved REMS application back to the correct dataset in DAISY.

## Deprecating an Exposure

Removing an exposure from a dataset is done by deprecating it, not deleting it. Deprecation requires a **reason**, which is stored alongside the deprecation timestamp. The exposure record is preserved in full — this is intentional, as it maintains an audit trail of which datasets were exposed, to which systems, and for how long.

Once all exposures for a dataset are deprecated, the dataset's publication status changes to *Deprecated*. It remains in DAISY but is no longer served to external systems via the API.

## Lifecycle Summary

```
Dataset created
      │
      ▼
[Unpublished] ──── Data Steward creates exposure ────▶ [Published]
                                                             │
                                              Data Steward deprecates exposure
                                                             │
                                                             ▼
                                                       [Deprecated]
```

!!! tip
    A deprecated dataset can be re-published by creating a new exposure. The previous deprecated exposure remains in the record history.
