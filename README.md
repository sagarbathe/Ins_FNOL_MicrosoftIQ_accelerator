# Auto FNOL Triage — Insurance Accelerator for Microsoft IQ

## Objective

Insurance carriers spend significant manual effort triaging First Notice of Loss (FNOL)
submissions — reading intake emails, looking up policy/coverage data, checking claim
history, spotting fraud/subrogation signals, and assigning the right adjuster. This
accelerator shows how **Microsoft IQ** (Fabric IQ + Foundry IQ + Work IQ, orchestrated by
a Copilot Studio agent) can automate that triage end-to-end for **Auto** insurance FNOL,
grounded in real policy/claim/vehicle/adjuster data and real policy-wording knowledge —
without any custom application code.

## What is Microsoft IQ?

<img width="845" height="474" alt="image" src="https://github.com/user-attachments/assets/0190a0bd-1190-4f6b-a413-0eb0da7efa30" />

Microsoft IQ is Microsoft's umbrella term for a set of composable, enterprise-grade
**agentic intelligence services** that can be combined to build business-specific AI
solutions. Each "IQ" specializes in a different kind of knowledge or action, and a
Copilot Studio (or M365 Copilot) agent orchestrates across all of them in a single
conversation:

| IQ | Purpose | Used in this accelerator for |
|---|---|---|
| **Fabric IQ** | Structured, governed enterprise data — queried via a knowledge/ontology graph over lakehouse data | Policy, policyholder, vehicle, claim, adjuster, fraud-signal, and subrogation-flag lookups by ID |
| **Foundry IQ** | Unstructured knowledge — documents, policy wording, playbooks, regulations, indexed and retrieved with reasoning | Coverage/exclusion wording, triage-tier rules, SIU fraud red flags, state regulatory rules, subrogation methodology |
| **Work IQ** | Microsoft 365 productivity signals and actions — mail, files, chat | Searching related emails/files for a claim, and sending claim correspondence |
| **Copilot Studio orchestrator** | Routes a user's question to the right IQ(s), combines results, and carries on the conversation | The "Auto FNOL Triage Agent" — the single entry point for adjusters, in Teams/M365 Copilot |

## High-Level Architecture

```
                         ┌───────────────────────────┐
   FNOL email  ────────► │   Copilot Studio Agent     │◄──── Adjuster chat (Teams / M365 Copilot)
   (Outlook)              │  "Auto FNOL Triage Agent" │
                         └─────────────┬─────────────┘
                                       │ routes by question type
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
┌───────────────┐            ┌──────────────────┐           ┌──────────────────┐
│   Fabric IQ    │            │    Foundry IQ     │           │     Work IQ       │
│ Ontology Data  │            │ Knowledge Agent    │           │  M365 Copilot /   │
│ Agent (MCP)    │            │ (MCP + Azure AI    │           │  Mail MCP tools    │
│                │            │  Search KB)        │           │                    │
│ Policy/Claim/  │            │ Policy wording,     │          │ Search emails/     │
│ Vehicle/       │            │ triage rules, SIU   │          │ files, send claim   │
│ Adjuster graph │            │ playbook, state     │          │ correspondence      │
│ (Fabric        │            │ regs, subrogation   │          │                     │
│ Lakehouse)     │            │ methodology (.md    │          │                     │
│                │            │ docs → AI Search    │          │                     │
│                │            │ index)              │          │                     │
└───────────────┘            └──────────────────┘           └──────────────────┘
```

**Routing logic:** questions naming a specific Policy/Claim/Adjuster ID go to **Fabric IQ**
first (real record lookups); general coverage/policy-concept or process questions go to
**Foundry IQ** first (knowledge retrieval); compound questions use both. Work IQ tools are
available throughout for mail/search actions.

## Configuration

No tenant-specific values (workspace/lakehouse/agent IDs, endpoints, resource names) are
hardcoded in this repo. Scripts read configuration from environment variables via
[`config.py`](config.py):

1. Copy [`.env.example`](.env.example) to `.env` in the repo root.
2. Fill in the required values (Fabric workspace/lakehouse IDs, Foundry project endpoint,
   Azure AI Search endpoint, Azure OpenAI endpoint) — these are specific to your tenant.
3. Everything else (display names like `LH_AutoFNOL`, `AutoFNOL_Ontology`, agent names, index
   names) has a sensible default already filled in, so you only need to set what's required.
4. For the Copilot Studio solution in `copilotstudio/`, replace the `<YOUR_FABRIC_...>`
   placeholders in `actions/InvokeAutoFNOLOntologyAgent.mcs.yml` with your own Fabric Data
   Agent ID and Workspace ID before importing.

## Components

- **`copilotstudio/`** — The Copilot Studio agent solution (`AutoFNOLAgent`): orchestration
  instructions, topics, and actions wiring together the Fabric ontology agent, the Foundry
  knowledge agent, and the two Work IQ MCP tools (M365 Copilot search, Outlook Mail).
- **`fabric/`** — Scripts to create the Fabric **ontology/graph model** over the lakehouse
  (Policy, Policyholder, Vehicle, Claim, Adjuster, FraudSignal, SubrogationFlag entities and
  their relationships) and configure/publish the **Fabric Data Agent** that serves it via MCP.
- **`foundry/`** — Knowledge base source docs (`kb_docs/*.md`: policy wording & exclusions,
  triage/adjuster-assignment rules, SIU fraud playbook, state regulatory requirements,
  subrogation methodology), the indexing pipeline into Azure AI Search, and the **Foundry
  Agent** creation/configuration scripts (including the required Activity Protocol +
  BotServiceRbac endpoint configuration needed for Copilot Studio/Teams integration).
- **`datagen/`** — Synthetic Auto FNOL dataset generator and lakehouse loader, producing the
  sample Policy/Policyholder/Vehicle/Claim/Adjuster/FraudSignal/SubrogationFlag/RepairShop data.
- **`documents/`** — Reference documentation for the accelerator:
  - `Auto_FNOL_Triage_Design_Document.docx` — solution architecture, Fabric/Foundry/Work IQ
    design details, Copilot Studio orchestration logic, and end-to-end workflow.
  - `Auto_FNOL_Prerequisites_and_Tenant_Readiness.docx` — required Azure/Fabric/Foundry/
    Copilot Studio/M365 setup steps and a generic tenant-readiness self-check (no
    tenant-specific names/IDs — see `.env.example` for how to plug in your own).
  - `Auto_FNOL_Sample_Emails.docx` — five ready-to-send sample FNOL intake emails covering
    different triage scenarios (fast-track, injury, fraud signal, subrogation, total loss),
    each with suggested follow-up questions to ask the Triage Agent to validate Fabric IQ,
    Foundry IQ, and Work IQ.
  - `Auto_FNOL_Deployment_Guide.docx` — the full, detailed step-by-step deployment procedure
    referenced in the [Deployment](#deployment) section below.

## Deployment

Full step-by-step instructions, including exact scripts to run and troubleshooting tips, are in
[`documents/Auto_FNOL_Deployment_Guide.docx`](documents/Auto_FNOL_Deployment_Guide.docx). Summary:

0. **Prerequisites** — Azure subscription/RBAC, Fabric capacity + workspace, Foundry project
   (chat + embedding model deployments) with Azure AI Search, Power Platform environment with
   Copilot Studio, and Microsoft 365 licenses/mailbox. See doc section *"0. Prerequisites"*.
1. **Configure your tenant** — copy `.env.example` to `.env` and fill in your Fabric
   workspace/lakehouse IDs and Foundry/Search/OpenAI endpoints (see [Configuration](#configuration)
   above). See doc section *"1. Configure Your Tenant (.env)"*.
2. **Generate & load sample data** — run `datagen/generate_fnol_data.py`, then
   `datagen/load_to_lakehouse.py` to populate the Fabric lakehouse. See doc section
   *"2. Generate & Load Sample Data (datagen/)"*.
3. **Build Fabric IQ** — create the ontology/graph with `fabric/create_ontology.py` (now
   includes the Claim→Adjuster relationship), configure and publish the Fabric Data Agent
   (`fabric/configure_data_agent*.py`), then validate via `fabric/test_mcp_dataagent.py`. See doc
   section *"3. Build the Fabric IQ Ontology & Data Agent (fabric/)"*.
4. **Build Foundry IQ** — index `foundry/kb_docs/*.md` with `foundry/build_search_index.py`, then
   create the Foundry Agent with `foundry/create_foundry_agent.py`, which now also enables the
   Activity Protocol automatically so the agent is immediately callable from Copilot Studio/Teams.
   See doc section *"4. Build the Foundry IQ Knowledge Agent (foundry/)"*.
5. **Deploy the Copilot Studio orchestrator** — `pac copilot push` the `copilotstudio/AutoFNOLAgent`
   solution, reconnect the Fabric/Foundry/Work IQ connection references (using the
   `<YOUR_FABRIC_...>` placeholders from Section 1), then `pac copilot publish` and enable the
   Teams channel. See doc section *"5. Deploy the Copilot Studio Orchestrator Agent
   (copilotstudio/)"*.
6. **Validate end-to-end** — test structured (Fabric), general-knowledge (Foundry), compound, and
   Work IQ questions in both Copilot Studio Test chat and Teams, using
   `documents/Auto_FNOL_Sample_Emails.docx` as ready-made scenarios. See doc section
   *"6. Validate End-to-End"*.
7. **Troubleshooting** — common errors (missing `.env` values, Foundry activity-protocol error, 429
   throttling, Fabric MCP failures, M365 Copilot Chat limitations) and fixes are in doc section
   *"7. Troubleshooting Quick Reference"*.
