# Cloud Mandate Workspace

The ENGAGE application now includes an internal **Mandate Workspace** page for operational use.

It is designed to preserve the existing Ambrosin workflow:

```text
COMMERCIAL MANDATE
        ↓
IDENTIFY
        ↓
PRIORITIZE / PARTNER
        ↓
ENGAGE
        ↓
ACTIVE OPPORTUNITY
        ↓
COMMERCIAL DEAL SHEET
        ↓
MANDATE REPORTING
```

Cloud persistence is optional. Portable JSON and Workspace Snapshot files remain supported as the fallback.

## What the cloud workspace stores

A saved workspace can contain:

- Commercial Mandate context
- current pipeline
- Business Development Execution updates
- Commercial Deal Sheets
- field-visit feedback
- next-action records used by the operational dashboard

These records may be commercially sensitive.

## Recommended backend

The current implementation supports a private Supabase project through its REST API.

Run:

```text
docs/supabase_workspace_schema.sql
```

in the Supabase SQL editor.

The schema enables Row Level Security and intentionally creates **no public policies**.

## Streamlit secrets

Configure the following only in Streamlit's server-side Secrets settings:

```toml
AMBROSIN_SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
AMBROSIN_SUPABASE_KEY = "YOUR_SERVER_SIDE_SERVICE_ROLE_KEY"
AMBROSIN_WORKSPACE_ACCESS_TOKEN = "A_SEPARATE_PRIVATE_WORKSPACE_PASSWORD"
AMBROSIN_SUPABASE_MANDATES_TABLE = "commercial_mandates"
AMBROSIN_SUPABASE_WORKSPACES_TABLE = "commercial_workspaces"
```

The two table-name variables are optional because the application already uses those names by default.

`AMBROSIN_WORKSPACE_ACCESS_TOKEN` is required before cloud persistence is considered enabled. It is deliberately separate from the Supabase credential. A user of the public Streamlit app must enter this private workspace token before the app can list, read or write cloud mandate records.

## Security

Do not:

- commit the Supabase key or Workspace Access Token to GitHub
- paste the service-role key into application source code
- expose the database credential in a browser-side application
- place the Workspace Access Token in query parameters or shared links
- disable RLS merely to make the REST calls work

The service-role key should exist only in server-side Streamlit secrets. It bypasses RLS and therefore must be treated as a privileged credential.

For a future multi-user client portal, replace this server-only model with authenticated users, organization/mandate ownership and explicit RLS policies.

## Current operational flow

1. Run the normal ENGAGE workflow.
2. Save a portable **Mandate Workspace Snapshot**.
3. Open the **Mandate Workspace** page from the Streamlit sidebar.
4. Open the snapshot.
5. Review the mandate funnel, next-action queue and active deal sheets.
6. Save/update the workspace in the private cloud backend.
7. In a later session, select the saved cloud workspace and resume the operational view.

## Next Action Queue

The workspace page classifies recorded actions as:

- Overdue
- Due Today
- Upcoming
- Unscheduled

It also assigns an operational priority using the current opportunity stage and the upstream commercial tier.

This is intentionally a workflow aid, not an autonomous CRM or automated outreach system.

## Design boundary

This persistence layer does not turn the portfolio into a public SaaS.

Its current purpose is to support Ambrosin Legal Trade's own execution of international Business Development mandates while preserving the same evidence-aware principles used across the four modules.


## Cross-module automatic handoff

After a mandate is saved to the private workspace, module navigation carries only the opaque `mandate_id` in the destination URL.

Example flow:

```text
IDENTIFY
  ↓  ?mandate_id=mandate_<opaque-id>
PRIORITIZE / PARTNER
  ↓  same mandate_id
ENGAGE
```

The receiving module resolves the canonical mandate from the private backend after Private Workspace Access is granted. The URL does not contain the client name, product, commercial objective, Supabase key or Workspace Access Token.

Portable Commercial Mandate JSON remains available as a fallback when cloud persistence is not configured or when a user intentionally wants an offline handoff.
