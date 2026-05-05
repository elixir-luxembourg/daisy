---
mount: /manual/gdpr_compliance
name: "GDPR Compliance"
---

<small>
[User guide](daisy.md) &raquo; *GDPR Compliance*
</small>

# GDPR Compliance in DAISY

GDPR places the burden of proof on the controller. It is not enough to believe you are compliant — you must be able to demonstrate it. For biomedical research institutions, this is a genuine challenge: data flows across many projects, partners, and jurisdictions; legal agreements accumulate; personnel change; and datasets outlive the projects they were originally collected for. DAISY was designed to close this gap — not by generating compliance reports after the fact, but by making structured record-keeping a natural part of day-to-day data management.

## The Organizing Principle: Processing Activities

The concept that shapes DAISY's entire design is the **processing activity** — the unit of analysis in Article 30's Record of Processing Activities (RPA). GDPR ties every compliance obligation to a specific purpose: the lawful basis is documented per purpose, retention periods are defined per purpose, and data subject rights are exercised in relation to a specific processing activity.

In DAISY, each **Project** represents one processing activity. When a research team registers a project, they are not simply creating an administrative record — they are opening an RPA entry. The project captures the purpose and scope of processing, the responsible personnel, the ethics and legal approvals, and the time period. Everything else in DAISY — datasets, contracts, legal bases, access records — anchors to a project and thereby to a defined processing purpose.

This matters practically. A dataset re-used for a new research question must be registered under a new project, because the purpose has changed and a fresh lawful basis determination is required. DAISY's structure makes this explicit rather than leaving it to institutional memory.

## Knowing What You Hold

Before an institution can protect personal data, it must know what it has. DAISY's **Dataset** entity provides this inventory. Each dataset documents the nature of the data with the level of granularity that is meaningful for compliance: what data types were received and generated, whether special-category data (Article 9) is present, whether subjects include minors or other vulnerable groups, what deidentification has been applied, and what the consent configuration looks like. Use conditions — downstream restrictions derived from the consent under which the data was collected — are also captured, encoded using GA4GH consent codes.

Retention is recorded as a concrete end-of-storage date. When that date approaches, DAISY notifies the responsible custodians, turning an abstract GDPR obligation into an actionable task.

## Contracts, Partners, and GDPR Roles

Research data rarely stays within a single organisation. DAISY's **Contract** entity captures the legal framework governing each data relationship. Contracts are linked to the project they support and to the external organisations — **Partners** — involved in the exchange. Each partner is assigned a GDPR role: *Controller*, *Joint Controller*, or *Processor*. Partners are also characterised by their geographic category — EU, non-EU, international — which is relevant to the transfer conditions of Chapter V GDPR.

Outbound data transfers are recorded in a **Transfer logbook** attached to the relevant dataset, capturing the recipient, governing contract, date, and applicable safeguards. This provides the auditable record of data flows required by Article 30.

## Legal Basis

Every processing activity must have a documented lawful basis before processing begins. DAISY records the Article 6 type, any Article 9 condition, the personal data categories covered, and a free-text justification.

!!! tip "One project, one purpose"
    One lawful basis applies per clearly defined purpose. If a project appears to require multiple bases, this is a signal that it contains multiple processing activities that should be split into separate DAISY Projects.

!!! note
    Legal basis is currently documented at the Dataset level. In a future release it will be moved to the Project level, which more precisely reflects the GDPR principle that the lawful basis is tied to the purpose of processing, not to the data itself.

## Evidence and Accountability

Demonstrating compliance during a supervisory authority inquiry or an internal audit requires more than structured data — it requires evidence. A **document repository** is attached to each Project, Dataset, and Contract. Ethics approval letters, consent forms, subject information sheets, signed data sharing agreements, and Data Protection Impact Assessments (required under Article 35 for high-risk processing) are all stored directly alongside the records they relate to. Documents carry expiry dates, and DAISY notifies custodians before they lapse.

Access to personal data is recorded as a first-class entity. Every grant of access to a dataset is captured with the grant date, expiry date, scope, and purpose notes. Access grants expire automatically, and approaching expiry triggers notifications. Changes to access records are written to an immutable **audit log**, making it possible to reconstruct the access history of a dataset at any point in time.

Storage locations are also documented — recording which server, cloud environment, or analysis platform holds each dataset — supporting both Article 32 obligations and data subject requests.

## Continuous Compliance

GDPR compliance degrades silently if it is not actively maintained. Consent forms expire. Ethics approvals lapse. Retention periods pass without action. DAISY's notification system is designed to prevent this: responsible custodians receive alerts before project end dates, storage duration deadlines, document expiry dates, and access grant expirations. The notification horizon and delivery channel — in-app or email — are configurable per user. The intent is that a data steward working from DAISY's notifications never needs to maintain a separate compliance calendar.

## Roles and Institutional Accountability

GDPR accountability requires that specific individuals can be identified as responsible for specific processing activities. Each Project, Dataset, and Contract in DAISY has assigned **Local Custodians** — the named individuals accountable for that record. Custodians receive notifications and hold elevated permissions on their records.

Beyond custodians, DAISY defines five user roles that reflect common institutional structures. Researchers can create and manage the records they are responsible for. Principal investigators additionally manage permissions on their own projects and datasets. Data Stewards have full system oversight and are typically the primary operators of DAISY on behalf of the institution. Legal users have elevated access specifically to contract records. Auditors have read-only access across all records and document attachments — designed for supervisory authority audits or internal compliance reviews.

Permissions propagate hierarchically: access to a Project carries through to its Datasets and Contracts. When a PI is responsible for a project, their accountability is automatically reflected across all data records under that project.

## Summary: GDPR Articles and DAISY Features

| GDPR Requirement | DAISY Feature |
|---|---|
| Art. 30 — Record of Processing Activities | Projects (one project = one processing activity) |
| Art. 30 — Data categories and subjects | Datasets |
| Art. 30 — Legal basis | Legal Basis records (currently on Datasets; future: Projects) |
| Art. 30 — Recipients and data transfers | Contracts, Partners, Transfer logbook |
| Art. 30 — Retention periods | End-of-storage field in Datasets + notifications |
| Art. 6 / 9 — Lawful basis | Legal Basis types covering Article 6 and Article 9 conditions |
| Art. 9 — Special-category data | Special-category flags and Personal Data Type classification |
| Art. 28 — Processor agreements | Contracts with GDPR role = Processor |
| Art. 32 — Access control | Access records, storage locations, expiry, audit log |
| Art. 35 — DPIA | Document type: Data Protection Impact Assessment |
| Art. 5(2) — Accountability | Audit trail, document repository, role-based access control |
