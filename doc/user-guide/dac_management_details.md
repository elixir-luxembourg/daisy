<small>
[User guide](daisy.md) &raquo; [Definitions](definitions_management_details.md) &raquo; *Data Access Committees*
</small>

# Data Access Committee (DAC) Management

A *Data Access Committee* (DAC) is a committee responsible for reviewing and approving data access requests for one or more datasets. In DAISY, a DAC is always linked to a *Contract*, which in turn belongs to a *Project*. DACs are managed under the **Definitions** module.

DACs are typically used in biomedical research to govern access to sensitive data — the committee reviews requests and decides who may access which datasets under what conditions.

## Creating a DAC

A DAC can be created in two ways:

- From the **Definitions** menu — navigate to the DACs tab and click the add button.
- From a **Contract detail page** — scroll to the DACs section and click the add button there. The contract is pre-filled.

When creating a DAC you must provide:

- **Title** — a unique name for the committee. The title cannot be changed after creation.
- **Project** — used to filter available contracts.
- **Contract** — the contract under which the DAC operates. Cannot be changed after creation.
- **Local Custodians** — at least one user responsible for managing the DAC.

Optionally, you may add a **Description** of the committee's purpose and scope.

!!! note
    DACs cannot be deleted once created.

## Managing Members

Committee members are *Contacts* (people registered in DAISY's Definitions module). To add a member:

1. Open the DAC detail page.
2. Click the add button in the **Members** section.
3. Select a contact and optionally add a remark (e.g. their role in the committee).

Each contact can only be added once per DAC. Members can be removed by users with edit permissions on the DAC.

## Linking Datasets

A DAC can be responsible for one or more *Datasets*. Datasets are linked to a DAC to indicate that the committee reviews and approves access requests for that data.

Assigning datasets to a DAC is restricted to **Data Stewards**. Only published datasets that are not already assigned to another DAC can be linked.

## Permissions

DAC permissions follow the same pattern as other DAISY records:

| Action | Who can perform it |
|--------|-------------------|
| View any DAC | All authenticated users |
| Create a DAC | Users with edit permission on the parent Contract |
| Edit a DAC | Data Stewards, Legal users (via contract), Local Custodians |
| Manage members | Same as edit |
| Assign datasets | Data Stewards only |

Permissions on a DAC are inherited from its parent Contract. If you have edit permission on a Contract, you have edit permission on all DACs under that contract. See [Users Groups and Permissions](user_management_details.md) for the full breakdown.
