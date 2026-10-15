# Business Development Execution & Outreach

### Mandate-Aware Outreach | Adaptive Cadence | Opportunity Execution | Commercial Reporting

**Operational focus:** Business Development Execution & Follow-Up

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://outreach-sequence-generator-eambrosin.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)
![Commercial Intelligence](https://img.shields.io/badge/Commercial%20Intelligence-ENGAGE-8250df)
[![Python CI](https://github.com/Eambrosin/outreach-sequence-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/Eambrosin/outreach-sequence-generator/actions/workflows/ci.yml)
[![Release](https://img.shields.io/badge/Release-v3.0.0-success)](https://github.com/Eambrosin/outreach-sequence-generator/releases/tag/v3.0.0)
[![License](https://img.shields.io/badge/License-All%20Rights%20Reserved-lightgrey)](LICENSE)

A Commercial Intelligence application that converts mandate and qualification context into adaptive multilingual outreach, qualified dialogue, follow-up and structured opportunity execution while preserving evidence, qualification gaps and channel availability.

> **Outreach should reflect what is known, what still needs to be qualified and which public channel is actually available.**

**[Launch the live application](https://outreach-sequence-generator-eambrosin.streamlit.app/)**

---

## Business Problem

Commercial outreach often breaks the connection between qualification and execution.

Typical problems include:

- every account receives the same cadence
- internal scores leak into prospect-facing messaging
- missing information is converted into confident claims
- channel selection ignores what is actually available
- follow-up intensity is disconnected from account priority
- multilingual messaging loses commercial context
- field activity and digital outreach operate separately

ENGAGE turns upstream qualification intelligence into a structured commercial sequence.

---


## Commercial Workflow

```text
COMMERCIAL MANDATE
        +
QUALIFIED BUYER / PARTNER PIPELINE
        ↓
ACCOUNT PRIORITY
        +
READINESS / GAPS
        +
AVAILABLE CHANNEL
        ↓
OUTREACH STRATEGY
        ↓
ADAPTIVE CADENCE
        ↓
RESPONSE / MEETING / FIELD FEEDBACK
        ↓
BUSINESS DEVELOPMENT EXECUTION LOG
        ↓
ACTIVE OPPORTUNITY
        ↓
COMMERCIAL DEAL SHEET
        ↓
MANDATE REPORTING
```

ENGAGE can consume qualified handoffs from PRIORITIZE and PARTNER and can also resume a previously saved Workspace Snapshot.

When a live Commercial Mandate is active but no real pipeline has been supplied, ENGAGE waits for the mandate-specific CSV or Workspace Snapshot instead of mixing demonstration accounts into live commercial work.

---

## Current Interface

The current live interface is organized around:

1. **Resume Workspace Snapshot** — restore a point-in-time execution workspace.
2. **Saved Commercial Mandate** — restore client, corridor, product and counterparty context from the shared private workspace.
3. **Upload Pipeline CSV** — load qualified buyer or partner records from upstream.
4. **Commercial Mandate Workspace** — keep the active mandate and stage visible.
5. **Executive Summary & Territory Execution** — review accounts, value context, priority, territory readiness and field-planning signals.
6. **Account & Business Development Workspace** — select an account and review the recommended commercial motion.
7. **Adaptive Outreach Sequence** — generate deterministic or optional AI-assisted prospect-facing copy.
8. **Business Development Execution Log** — record responses, meetings, objections, qualification evidence and next actions.
9. **Commercial Deal Sheet** — structure active commercial terms without turning assumptions into facts.
10. **Commercial Mandate Reporting** — track the mandate funnel and produce client-ready operational reporting.

---

---

## Ambrosin Commercial Mandate Workspace

ENGAGE is the execution layer of the shared **Commercial Mandate Workspace**.

A saved mandate can be selected directly or opened from IDENTIFY, PRIORITIZE or PARTNER through an opaque **mandate_id**. After **Private Workspace Access** is granted, the canonical mandate is restored from the private Supabase-backed workspace.

The current input hierarchy is:

1. **Workspace Snapshot**, when resuming a previous operational session
2. **Saved Commercial Mandate** from the shared workspace
3. optional portable Commercial Mandate JSON override
4. qualified Pipeline CSV from PRIORITIZE / PARTNER

The mandate remains attached while the workflow progresses from outreach to response, meeting, opportunity, deal sheet and reporting.

Recommended progression:

```text
PRIORITIZE / PARTNER
        ↓
      ENGAGE
        ↓
Qualified Dialogue
        ↓
Active Opportunity
        ↓
Commercial Deal Sheet
        ↓
Mandate Reporting
```

---

## Workspace Snapshot

ENGAGE can save the active Business Development operation as a portable **Mandate Workspace Snapshot**.

The snapshot preserves:

- Commercial Mandate context
- current pipeline records
- Business Development execution updates
- Commercial Deal Sheets
- field-visit feedback
- source metadata

A saved snapshot can be uploaded later to resume the same workspace after the Streamlit session has ended.

The snapshot is a portable recovery and handoff layer that complements the shared Supabase-backed workspace. It preserves a point-in-time operational state for portability, recovery and controlled transfer between sessions.

Because snapshots may contain commercially sensitive information, they should be stored and shared according to the confidentiality requirements of the mandate.

---

## Core Capabilities

- qualification-aware outreach strategy
- priority-based cadence
- available-channel selection
- multilingual outreach
- account-specific message generation
- qualification-first messaging
- deterministic fallback generation
- optional AI-assisted copy
- territory and field-sales context
- field-day planning
- visit / meeting feedback loop
- Business Development Execution Log
- Commercial Deal Sheet
- Commercial Mandate Reporting
- mandate funnel and client-ready reporting
- shared private Ambrosin Commercial Mandate Workspace
- automatic mandate restoration through `mandate_id`
- Supabase-backed mandate persistence
- mandate-safe pipeline behavior
- portable Commercial Mandate JSON
- portable upstream handoffs
- CSV import / export
- automated tests and GitHub Actions CI
- full-history secret scanning

---

## Two Operating Modes

### Commercial Intelligence Mode

Consumes structured context such as:

- account priority
- Qualification Readiness
- Buyer Access
- Sales Motion
- qualification questions
- evidence gaps
- account / territory context
- counterparty role
- Commercial Mandate context

This mode is designed to preserve upstream commercial reasoning. A portable mandate JSON can also be loaded directly when the pipeline itself does not already contain mandate metadata.

### Standard Outreach Mode

Creates outreach directly from account inputs when an upstream handoff is not available.

This keeps the application usable as a standalone system.

---

## Business Development Execution Log

ENGAGE now continues beyond first-touch outreach.

For each selected counterparty, the workflow can record:

- opportunity stage
- response status
- meeting / conversation outcome
- observed commercial interest
- products / solutions discussed
- decision process and stakeholders
- budget / investment status
- commercial timeline
- technical questions
- objections / blockers
- requested documents
- next commercial action
- next-action date
- execution notes

The resulting **BD Execution Update** is exportable and preserves the Commercial Mandate and Trade Feasibility context.

```text
CONTACT
  ↓
RESPONSE
  ↓
QUALIFICATION
  ↓
MEETING
  ↓
FOLLOW-UP
  ↓
ACTIVE OPPORTUNITY
  ↓
NEXT ACTION
```

---

## Commercial Deal Sheet

When a conversation becomes an active opportunity, ENGAGE can structure the commercial negotiation in a **Commercial Deal Sheet**.

The deal sheet can preserve:

- product / technical scope
- quantity
- indicative commercial value and currency
- quotation / proposal status
- Incoterm, when discussed
- payment terms
- MOQ
- delivery / lead-time terms
- warranty
- after-sales / technical-support model
- exclusivity and territory terms
- commission / success-fee terms
- technical and regulatory validation status
- documents exchanged
- decision makers / stakeholders
- commercial risks
- next step and next-step date

Mandate context and Trade Feasibility status remain attached to the deal.

The sheet organizes negotiation context; it does not generate legal conclusions or substitute contract review.

---

## Commercial Mandate Reporting

ENGAGE can aggregate the currently loaded pipeline together with execution updates and deal sheets into an operational mandate report.

Current indicators include:

- counterparties in pipeline
- qualified counterparties
- high-priority counterparties
- contacted accounts
- responses
- meetings
- active opportunities
- quotations / proposals
- wins
- indicative opportunity value by currency
- next-action queue
- top recorded opportunities

Reports can be exported as Markdown, including a client-ready Ambrosin mandate report with reporting period, mandate context, funnel, indicative opportunity value, priority opportunities and next actions. Execution updates and deal sheets remain exportable as CSV.

Metrics reflect records entered or loaded in the workflow. They are not market-size, buyer-demand or conversion-rate claims.

---

## Qualification-First Design

ENGAGE distinguishes between:

**What is known**  
Observed or explicitly supplied account information.

**What should be qualified**  
Commercially relevant information that still requires a conversation.

**What should not be claimed**  
Internal scores, unsupported buying intent, unverified decision authority or unobserved needs.

This prevents internal prioritization logic from becoming external prospect-facing language.

---

## Channel & Cadence Logic

The application can adapt around channels such as:

- LinkedIn
- email
- phone
- WhatsApp
- field visit

Channel selection should reflect observed availability and the commercial context of the account.

Cadence intensity can also vary by priority instead of applying a universal sequence to every account.

---

## Multilingual Execution

The system supports commercial outreach across multiple languages and can preserve:

- qualification objective
- tone
- account context
- CTA
- channel constraints
- sequence continuity

Language generation is treated as an execution layer rather than a replacement for commercial strategy.

---


## PRIORITIZE / PARTNER → ENGAGE

ENGAGE is designed to consume qualified execution context rather than restart research.

**From PRIORITIZE**, it can preserve:

- ICP / commercial priority
- score rationale and tier
- Qualification Readiness
- Buyer Access / Sales Motion
- qualification gaps
- recommended action
- Commercial Mandate context

**From PARTNER**, it can preserve:

- partner role and archetype
- strategic fit and market-access context
- route-to-market readiness
- due-diligence gaps
- technical / after-sales capability
- recommended partner-development action
- Commercial Mandate context

IDENTIFY evidence can still travel downstream through these handoffs. The objective is continuity: research, qualification, partner validation and execution should not be rebuilt at every stage.

---


## Architecture

```text
app.py
  ↓
workspace_persistence.py / mandate_workspace.py
  ↓
workspace_cloud.py / workspace_snapshot.py
  ↓
upstream pipeline normalization
  ↓
outreach_generator.py
  ↓
adaptive cadence + message generation
  ↓
field_planner.py / visit_feedback.py
  ↓
bd_execution.py / commercial_deal.py
  ↓
mandate_reporting.py / client_reporting.py
```

Deterministic commercial logic remains available without an AI key. Shared workspace persistence handles mandate context, while Workspace Snapshots preserve a portable point-in-time operational state.

---

## Testing

The repository includes automated tests for:

- outreach generation
- field planning
- visit feedback
- deterministic fallbacks
- handoff behavior

Run locally:

```bash
python -m pytest -q
```

GitHub Actions runs CI on pushes and pull requests to `main`.

---

## Running Locally

```bash
git clone https://github.com/Eambrosin/outreach-sequence-generator.git
cd outreach-sequence-generator
pip install -r requirements.txt
streamlit run app.py
```

Optional AI features require the relevant API key in environment variables or Streamlit secrets.

---


## Current Version

**v3.0.0 — Business Development Execution & Outreach**

Version 3.0 is the current stable release of ENGAGE. It expands the application from adaptive outreach into the operational execution and reporting layer of the Commercial Intelligence portfolio.

Key release capabilities include:

- shared private Commercial Mandate and workspace persistence
- automatic `mandate_id` restoration
- qualified pipeline intake from PRIORITIZE and PARTNER
- mandate-safe behavior with no demo-data mixing
- Workspace Snapshot recovery
- adaptive multilingual outreach
- Business Development Execution Log
- field-visit feedback loop
- Commercial Deal Sheet
- opportunity and next-action management
- mandate funnel and client-ready reporting

**[View v3.0.0 Release](https://github.com/Eambrosin/outreach-sequence-generator/releases/tag/v3.0.0)**  
[Release Notes](docs/RELEASE_NOTES_v3.0.0.md)

---

## Documentation

- [v3.0.0 Release Notes](docs/RELEASE_NOTES_v3.0.0.md)
- [Detailed Technical Reference](docs/TECHNICAL_REFERENCE.md)
- [Portfolio Demo Flow](docs/PORTFOLIO_DEMO.md)
- [Tests](tests/)
- [Commercial Intelligence Portfolio](https://github.com/Eambrosin)

---

## Limitations

This is a portfolio and commercial decision-support application.

It does not:

- autonomously send outreach
- verify private contact information
- infer buying intent
- guarantee that a public channel is current
- replace human review before external communication

---

## Portfolio Context

This project is the **ENGAGE / EXECUTE** layer of the Commercial Intelligence portfolio:

```text
IDENTIFY → PRIORITIZE → ENGAGE
IDENTIFY / Partner Universe → PARTNER → ENGAGE
```

**IDENTIFY:** [Market Entry & Opportunity Intelligence](https://github.com/Eambrosin/opportunity-discovery-intelligence)  
**PRIORITIZE:** [Counterparty Qualification & Commercial Priority](https://github.com/Eambrosin/lead-qualification-scorer)  
**Portfolio:** [github.com/Eambrosin](https://github.com/Eambrosin)

---

## Author

**Eduardo Ambrosin**  
International Business Development | Strategic Partnerships | GTM | Commercial Intelligence
