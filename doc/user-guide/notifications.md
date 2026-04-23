# Notifications

DAISY monitors key dates across records and automatically notifies local custodians before deadlines are reached. This helps research teams stay ahead of data retention obligations, expiring agreements, and access grants — without having to track dates manually.

## What triggers a notification

| Entity | Event |
|--------|-------|
| **Project** | Project start date, project end date |
| **Dataset / Data Declaration** | Embargo date, end of storage duration |
| **Access** | Grant expiration date (active grants only) |
| **Document** | Document expiry date (on Projects and Contracts) |

Notifications are generated daily. Each user receives a notification when an event falls within their configured advance notice window (default: **90 days**).

## Who receives notifications

Notifications are sent to the **local custodians** of the affected record:

- Project events → project local custodians
- Dataset and access events → dataset local custodians and the project's local custodians
- Document events → local custodians of the project or contract the document is attached to

## Viewing notifications in DAISY

In-app notifications appear in the DAISY interface and can be dismissed individually or all at once for a given record type. Dismissed notifications can be shown again by toggling the "Show dismissed notifications" option.

## Email notifications

If email notifications are enabled in your settings, DAISY sends a daily digest at 07:00 listing all your pending upcoming events. The email groups notifications by record type (Projects, Datasets, Accesses, Documents) and shows the event date and a description of what is approaching.

## Configuring your notification preferences

Go to your profile and open **Notification settings**. You can adjust:

| Setting | Description | Default |
|---------|-------------|---------|
| **Send email** | Receive a daily email digest of upcoming events | Off |
| **Send in-app** | Show notifications inside DAISY | On |
| **Advance notice (days)** | How many days before an event you are notified | 90 |

The advance notice setting applies to all event types. For example, with the default of 90 days, you will be notified about a dataset's end of storage 90 days before that date is reached.

!!! note
    Your DAISY administrator can disable all email notifications system-wide. If you enable email but are not receiving messages, contact your administrator.
