---
mount: manual/users_group
name: "What are the users groups?"
---


# What are the users groups?

DAISY provides various types of users accounts with assigned different sets of users actions. Generally, any user can view DAISY records and create a project, thus become the project's *owner*. The owner is granted for managing the project. If *standard user* is appointed as project's *local custodian*, his privileges become equal to project's owner - thus he can manage the project too. Standard user by default is not allowed to access the documents attachments.

The extension of standard user is *VIP user*. By default, if VIP user is project's owner or local custodian, he is granted for project's administrator, thus can manage users access/permissions for the project. Moreover, VIP has access to view and manage the documents attachments.

Below we specified the users privileges:
<!-- This is the default role assigned to all users. All DAISY users can view all Dataset, Project, Contract and Definitions. The document attachments of records are excluded from this view permission. -->
- **Standard user**
The default group that users are assigned to. All DAISY standard users can:
	- view any *Dataset*, *Project*, *Contract* or *Definition* (further called *modules* or *records*). The documents attachments of the records are protected, thus excluded from the view permission.
	- create any module.
	- edit and delete any module the user has created.
	- if user is assigned as *Local Custodian*, he is granted for the permissions to edit and delete the module.
	- has no access to grant other users with the projects's permissions (even for the modules the user owns or is *Local Custodian*).

- **VIP user**
The research principle investigators are typically assigned to this group. VIP users have:
	- all privileges (view, add, edit, remove) on the records they own, meaning the records where the user has been appointed as the *Local Custodian* or the projects he created.
	- view and manage the protected documents attachments of modules he owns.
	- grant other users with permissions on the datasets and projects he owns (VIP is the project's administrator).

NOTE: Being a local custodian or owner extends the users permissions in the similar way. For the standard user, it grants for edit and delete records. For VIP user to edit, delete records and project/dataset administration.

- **Legal user**
The users assigned to this group can are allowed to manage *Contract* records. Legal personnel can:
	- add, view, edit and remove any contract.
	- grant the other users with an access for the contract.
	- view all records in DAISY and manage their documents attachments.

	If you are legal user we suggest to read firstly the [DAISY Overview](daisy.md) and then the [Contract Management](contract_management_details.md) section.

For more details go to [Users Groups and Permissions](user_management_details.md) (recommended for DAISY superuser).
