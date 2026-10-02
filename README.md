# Adaptive Outreach Intelligence Platform

### Commercial Prioritization | Adaptive Cadence | Multilingual Outreach | Qualification-First Execution

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://outreach-sequence-generator-7dcmglcxfnmszlodg8lqre.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)
![Commercial Intelligence](https://img.shields.io/badge/Commercial%20Intelligence-ENGAGE-8250df)
[![Python CI](https://github.com/Eambrosin/outreach-sequence-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/Eambrosin/outreach-sequence-generator/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-All%20Rights%20Reserved-lightgrey)](LICENSE)

A Commercial Intelligence application that converts qualification context into adaptive, multilingual outreach sequences while preserving evidence, qualification gaps and channel availability.

> **Outreach should reflect what is known, what still needs to be qualified and which public channel is actually available.**

**[Launch the live application](https://outreach-sequence-generator-7dcmglcxfnmszlodg8lqre.streamlit.app/)**

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
QUALIFICATION CONTEXT
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
MULTILINGUAL TOUCHES
        ↓
NEXT ACTION
        ↓
VISIT / RESPONSE FEEDBACK
```

The system can work independently or consume upstream handoffs from IDENTIFY and PRIORITIZE.

---

## Product Preview

### 1. Executive Outreach Intelligence

![Executive Summary](screenshots/v2-executive-summary.png)

A concise view of outreach priority, readiness, channel availability and commercial next actions.

### 2. Adaptive Priority Ranking

![Priority Ranking](screenshots/v2-priority-ranking.png)

Accounts are ordered using upstream commercial context rather than treating every prospect equally.

### 3. Account & Outreach Intelligence

![Account Intelligence](screenshots/v2-account-intelligence.png)

Brings account context, qualification gaps, channel strategy and messaging logic into one workspace.

### 4. Adaptive Cadence

![Adaptive Cadence](screenshots/v2-adaptive-cadence.png)

Cadence changes according to commercial priority, qualification state and available engagement paths.

### 5. Generated Outreach Sequence

![Generated Sequence](screenshots/v2-generated-sequence.png)

Creates a multilingual sequence that preserves qualification-first language and avoids exposing internal scoring.

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
- visit-feedback loop
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

This mode is designed to preserve upstream commercial reasoning.

### Standard Outreach Mode

Creates outreach directly from account inputs when an upstream handoff is not available.

This keeps the application usable as a standalone system.

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

## IDENTIFY / PRIORITIZE → ENGAGE

ENGAGE can receive context from:

**IDENTIFY — Opportunity Discovery Intelligence**

- account identity
- public-contact evidence
- Account Opportunity
- Qualification Readiness
- Buyer Access
- Sales Motion
- qualification questions
- evidence gaps

**PRIORITIZE — Lead Qualification & Revenue Prioritization**

- ICP fit
- commercial score
- priority tier
- revenue context
- recommended action
- qualification gaps

The objective is to avoid restarting research at the outreach stage.

---

## Architecture

```text
app.py
  ↓
upstream handoff / direct account input
  ↓
outreach_generator.py
  ↓
adaptive cadence + message generation
  ↓
field_planner.py
  ↓
visit_feedback.py
```

Deterministic commercial logic remains available even when the optional AI layer is disabled.

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

**v2.1.0 — Adaptive Outreach Intelligence**

Current functionality includes qualification-aware handoffs, account intelligence, priority-based cadence, multilingual execution, field-sales context and stronger evidence-aware outreach behavior.

Release notes are available in [docs/RELEASE_NOTES_v2.1.0.md](docs/RELEASE_NOTES_v2.1.0.md).

---

## Documentation

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

This project is the **ENGAGE** layer of the Commercial Intelligence portfolio:

```text
IDENTIFY → PRIORITIZE → ENGAGE
IDENTIFY / Partner Universe → PARTNER → ENGAGE
```

**IDENTIFY:** [Opportunity Discovery Intelligence](https://github.com/Eambrosin/opportunity-discovery-intelligence)  
**PRIORITIZE:** [Lead Qualification & Revenue Prioritization](https://github.com/Eambrosin/lead-qualification-scorer)  
**Portfolio:** [github.com/Eambrosin](https://github.com/Eambrosin)

---

## Author

**Eduardo Ambrosin**  
International Business Development | Strategic Partnerships | GTM | Commercial Intelligence
