# Create AI Agents Championship — Preparation

**Project:** SHPAIZMAN ORCHESTRATOR
**Project lead:** Alexander Viktorovich Negriy
**Suggested category to review:** Best Business AI Agent. Category selection and eligibility must be confirmed in the official application.

## Problem and proposed solution

Small service businesses have to qualify requests, define scope, coordinate technical work and track delivery. SHPAIZMAN aims to help a human operator prepare and track this workflow across specialist roles with local control and a clear approval boundary.

The repository currently demonstrates an **offline, deterministic prototype**. It includes a ten-role registry, a local SQLite planning queue, a service-order workflow, local integrity checks and a stop control. It does not currently call an AI model or verify any live provider account. The full Windows GUI and adapters are described as a separate package and have not been verified on the intended computer.

## Reproducible demonstration

From a Python 3.12 checkout:

```bash
python -m unittest discover -s tests -v
python -m shpaizman.demo
```

The demo uses a temporary database and a fictional CRM request. It checks that processing starts stopped, creates one deterministic draft after a local operator acknowledgement, stops processing, advances one synthetic service request to qualification, and verifies the local journal. The acknowledgement is not authenticated approval; the synthetic contact-consent assertion is not real client consent. No model, external provider, customer, message or payment is involved.

## Submission checklist

- [ ] Confirm participant registration and category in the official platform. No registration or submission is claimed here.
- [ ] Build and demonstrate an actual AI-agent capability: choose an authorized model and evaluate its outputs and failure behavior. Model availability and cost limits must be verified.
- [ ] Validate authorized Windows installation, one real provider integration and recovery behavior; collect independent evidence.
- [ ] Prepare an English pitch deck and demo video showing the real product and its limitations.
- [ ] Define a measured business outcome, collect a baseline and compare results on representative tasks. Demo runtime alone is not proof of money saved.
- [ ] Review rights, third-party licenses, privacy and security before using real client data or publishing release materials.

## Official guidance checked on 2026-11-17

The [Dubai Chamber of Digital Economy's championship page](https://www.dubaichamberdigital.com/en/create-ai-agents) describes free registration, English submissions, a prototype, pitch deck and demo video, and says a fully working AI agent is expected at the Grand Final. Its page lists registration and submission in January 2027. A [Dubai government announcement](https://protocol.dubai.ae/en/media-listing/news-events/hamdan-bin-mohammed-launches-create-ai-agents-championship-to-inspire-transformative-ideas-for-global-good/) says registration closes in December 2026. Because these official sources differ, verify the current deadline directly on the official application platform; do not assume registration or eligibility is complete.
