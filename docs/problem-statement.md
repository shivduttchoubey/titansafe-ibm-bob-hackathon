# Problem Statement

## Background

Social media platforms are the primary coordination surface for offline violence in India.
The 2020 Delhi riots, the 2022 Nupur Sharma controversy, and repeated election-cycle
misinformation campaigns all followed the same pattern: coordinated inauthentic accounts
amplify incitement content in tight bursts, then the offline event happens before law
enforcement has actionable intelligence.

India's **DPDP Act 2023** (Digital Personal Data Protection Act) creates a new legal tension:
platforms are data fiduciaries with strong minimisation and safeguard obligations
(s.8(5)), yet investigation exemptions (s.17) do not override those obligations —
they merely restrict the data principal's rights. Bulk raw data dumps are legally
indefensible and operationally dangerous.

## The Problem

Law enforcement agencies investigating coordinated incitement, targeted harassment
(doxxing), or organised misinformation on social media have two bad choices today:

1. **Ask for nothing** — and lose the 30–90 minute window before an offline event
   that a real-time signal would have enabled them to act on.
2. **Ask for everything** — a bulk data dump of all posts, phone numbers, emails and
   social graphs — which violates DPDP obligations, exposes thousands of innocent
   users, and creates an audit trail of mass surveillance that platforms cannot
   legally provide.

There is no privacy-preserving, cryptographically verifiable middle path.

## Who is Affected

- **State Cyber Cells and district-level officers** who need timely, precise threat
  intelligence to prevent offline violence but lack a lawful, proportionate way to
  obtain it from platforms.
- **Platforms (data fiduciaries)** that want to cooperate with legitimate LEA requests
  but have no technical mechanism to share exactly what is needed while protecting
  uninvolved users.
- **Ordinary users** whose data is swept up in bulk disclosures even when they have
  no connection to any coordinated campaign.
- **Journalists and activists** who are disproportionately targeted by doxxing campaigns
  and whose safety depends on platforms not handing over their data without strict gates.

## Why It Matters

- Coordinated incitement clusters have preceded lethal offline violence within hours
  of the first post. A 30-minute detection-and-escalation window is the difference
  between prevention and response.
- Bulk data sharing creates a chilling effect on lawful speech and is a vector
  for misuse by bad-faith actors within or connected to law enforcement.
- India has 900 million+ internet users; the scale of collateral exposure from
  undiscriminating disclosure is enormous.

## Why Existing Solutions Fall Short

- **Manual LEA requests** take days to weeks and arrive with far more data than needed.
- **Platform transparency reports** are aggregate and retrospective — useless for
  real-time threat response.
- **Ad-hoc redaction** by platform trust-and-safety teams has no cryptographic
  verifiability: the LEA has no way to confirm that the evidence wasn't altered after
  the fact.
- **No existing solution** combines real-time CIB detection, tiered proportional
  disclosure, zero-knowledge proofs of cluster scale, and a tamper-evident audit
  chain in a single, deployable, zero-dependency Python package.
