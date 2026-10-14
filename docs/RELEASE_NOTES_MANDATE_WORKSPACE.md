# Release Notes — Mandate Workspace Operational Layer

## Added

### Ambrosin Commercial Mandate Workspace page

ENGAGE now includes an internal Streamlit page that can open a portable Workspace Snapshot or resume a saved cloud workspace.

The page consolidates:

- mandate context
- Researched → Qualified → Contacted → Responses → Meetings → Opportunities → Quotations → Won
- indicative pipeline value
- Commercial Deal Sheets
- client-ready reporting
- portable snapshot export

### Next Action Queue

Execution updates are converted into an operational queue with:

- company
- current opportunity stage
- next action
- due date
- working priority
- Overdue / Due Today / Upcoming / Unscheduled status

Overdue actions are surfaced before upcoming actions.

### Private cloud persistence

A new optional persistence layer supports storing complete ENGAGE workspace snapshots in a private Supabase backend.

Portable Workspace Snapshots remain the fallback and the cloud backend is not required for the app to operate.

### Security-first database setup

The provided Supabase schema:

- enables Row Level Security
- creates no anonymous policies
- is intended for server-side access only
- keeps the privileged key out of GitHub and browser-side code

### Shared portfolio contract

The AI Business Development Toolkit now contains a formal **Commercial Mandate Workspace Contract v1** defining workspace identity, snapshot structure, operational boundaries and module responsibilities.

## Design boundary

This release does not turn the portfolio into a public SaaS.

The operational goal remains to support Ambrosin Legal Trade in executing real international Business Development mandates while preserving evidence-aware research and human commercial judgment.
