# Data Access Committee (DAC) in DAISY

## Overview

A **Data Access Committee (DAC)** is responsible for reviewing and approving data access requests for datasets in DAISY. Each DAC is linked to a contract and project, has local custodians (users), and can have members (contacts). DACs are central to managing dataset access and compliance.

---

## Creating a DAC

- **From the DACs page:**  
  Users with the same permissions as for contracts (i.e., users who can create/edit the associated contract) can create a new DAC using the "Add DAC" button.
- **From a Contract page:**  
  On a contract's detail page, use the "Create new DAC for contract" button. This opens a modal form pre-filled with the contract and project.

**Required fields:**

- Title (unique)
- Contract (must belong to the selected project)
- At least one local custodian

**Form:**  
Uses [`core.forms.dac.DACForm`](../core/forms/dac.py).  
Validation ensures the contract matches the project and at least one local custodian is selected.

---

## Editing a DAC

- Only users who can edit the associated contract can edit a DAC (the same permissions as for contracts).
- Fields like project, contract, and title are disabled in edit mode for integrity.
- Edit via the DAC detail page using the "Edit DAC" button.

**Form:**  
Uses [`core.forms.dac.DACFormEdit`](../core/forms/dac.py).

---

## Adding a DAC from a Contract

- On the contract detail page, click "Create new DAC for contract".
- The modal form will be pre-populated with the contract and project.
- After creation, the DAC is linked to the contract and visible in the contract's DAC list.

---

## Adding and Removing Members

- **Add Member:**  
  On the DAC detail page, click "Add member to DAC".  
  Fill in the contact and an optional remark.  
  **Anyone with edit DAC permission** can add members.
- **Remove Member:**  
  Use the delete icon next to a member in the members table.  
  **Anyone with edit DAC permission** can remove members.

**Memberships:**

- Managed via the [`core.models.dac.DacMembership`](../core/models/dac.py) model.
- Each contact can only be a member of a DAC once (unique constraint).
- Memberships store the date added and a remark.

---

## Adding and Removing Datasets

- **Add Dataset to DAC:**  
  Only users with the `is_data_steward` permission can add datasets to a DAC.  
  On the DAC detail page, click "Add Dataset to DAC" and select a published dataset.
- **Remove DAC from Dataset:**  
  Once a dataset is assigned to a DAC, it cannot be removed (enforced by model validation).

**Technical details:**

- The dataset's `dac` field is a foreign key to DAC.
- Assignment is handled by the `pick_dataset_for_dac` view, which requires `is_data_steward`.
- Attempting to remove a DAC from a dataset raises a validation error.

---

## Permissions

- **Creating/Editing DACs:**  
  The same users who can create or edit the associated contract can create or edit a DAC.
- **Adding/Removing Members:**  
  Anyone with edit DAC permission can add or remove DAC members.
- **Adding Datasets:**  
  Requires `is_data_steward` permission.

---

## References

- [DAC model](../core/models/dac.py)
- [DAC forms](../core/forms/dac.py)
- [DAC views](../web/views/dacs.py)
- [DAC tests](../web/tests/test_dac.py), [DAC view tests](../web/tests/views/test_dac_views.py)
- [DAC templates](../web/templates/dac/)

---
