# n8n Agency Automations

Production-ready n8n workflow templates built for marketing agencies to resell to clients. Each workflow ships with the exported JSON, setup docs, and a sales sheet.

## Workflows

| Workflow | Status | Docs | Sales sheet |
|---|---|---|---|
| [AI Speed-to-Lead Engine](workflows/ai-speed-to-lead-engine.json) | ✅ Built & tested | [docs](docs/ai-speed-to-lead-engine.md) | [sales](sales/ai-speed-to-lead-engine.md) |

## How these are built

- Nodes, names, emails and docs are all in English (US clients).
- No API keys are ever committed — every workflow uses n8n's credential system, and each doc lists exactly which credentials the client needs to create.
- All client-specific settings (agency name, emails, tone, thresholds, links, IDs) live in a single `⚙️ CONFIG` node per workflow, so reselling = duplicate + edit one node.
- Every workflow has an Error Trigger wired to Slack + email alerts, and retries (3x) on HTTP/AI/CRM calls.
- Sticky Notes explain every block directly on the canvas.
- Structural validation (`n8n_validate_workflow`) passes with 0 errors before delivery; execution is tested with realistic data and checked via `n8n_executions`.

## Repo layout

```
/workflows/<name>.json   — exported n8n workflow, ready to import
/docs/<name>.md          — what it does, credentials, 10-minute setup, cost estimate
/sales/<name>.md         — 3-sentence pitch, ROI, pricing, 90s Loom script
/screenshots/            — proof-of-test screenshots
```
