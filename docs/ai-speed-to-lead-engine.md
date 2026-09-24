# AI Speed-to-Lead Engine

Responds to and qualifies every inbound lead in under 60 seconds, 24/7 — before your competitors even open their inbox.

## What it does

1. **Intake** — a Webhook accepts POSTs from a website contact form, Typeform, or Facebook Lead Ads. A normalization step auto-detects the payload shape and maps it to one standard lead object (`name, email, phone, company, website, message, source`).
2. **Instant response** — the webhook replies `200 {"status":"received"}` immediately after normalization. The form/integration never waits on AI or CRM calls; everything below runs in the background of the same execution.
3. **Deduplication** — looks up the lead's email in a Google Sheet (your lightweight CRM). If it already exists, the contact record is updated and no duplicate emails/alerts go out. A disabled HubSpot branch shows how to swap in a real CRM instead.
4. **Website enrichment (optional)** — if the lead gave a website, the workflow fetches the homepage and extracts the `<title>` and meta description for extra context. If the site is missing or unreachable, it continues with empty enrichment — never blocks the pipeline.
5. **AI qualification** — an LLM (OpenAI, model configurable) scores the lead 0–100 and classifies it `hot` / `warm` / `cold`, using criteria you define in plain English. Output is forced into structured JSON (score, tier, intent, budget_signal, summary, recommended_next_step) and validated; if parsing ever fails, a safe `warm` fallback is used so no lead is silently lost.
6. **Tier routing:**
   - **HOT** → Slack alert to your sales channel (with AI summary + booking link) and a personalized email to the lead with your Calendly link, both within seconds.
   - **WARM** → a personalized first email, then a 3-email follow-up sequence (Wait 2 days → email 2 → Wait 3 days → email 3), automatically stopping if the lead responds (tracked via a `responded` column in the sheet).
   - **COLD** → one short, no-hard-sell educational email, and a `cold` tag in the CRM sheet.
7. **Logging** — every lead is recorded in the Google Sheet with timestamp, score, tier, emails sent, and response time in seconds, so you can measure actual speed-to-lead.
8. **Error handling** — any node failure (after 3 automatic retries on HTTP/AI/CRM calls) triggers a Slack + email alert with the workflow name, failing node, and error message.

## Credentials the client needs to create

All client-specific values (agency name, Calendly link, Slack channel, email sender, qualification criteria, score thresholds, AI model, follow-up timing) live in **one node: `⚙️ CONFIG`**. Nothing else needs to be touched to resell or re-brand this workflow.

| # | Credential | Used for | Where to get it |
|---|---|---|---|
| 1 | Google Sheets OAuth2 | CRM log + duplicate check | Google Cloud Console → OAuth client, or use n8n's built-in Google OAuth connect flow |
| 2 | Slack API (Bot Token) | Hot-lead + error alerts | Create a Slack App → OAuth & Permissions → Bot Token (scope `chat:write`), invite the bot to your alert channel |
| 3 | SMTP | Outbound lead emails | Any SMTP provider (Gmail app password, SendGrid, Postmark, Mailgun SMTP, etc.) |
| 4 | OpenAI API | Lead qualification + email writing | platform.openai.com → API keys |

> The `Slack - Error Alert` and `Send Email - Error Alert` nodes have their channel/inbox **hardcoded** (not in CONFIG) — this is intentional. n8n's Error Trigger runs in its own isolated execution and cannot read the CONFIG node from the failed run, so these two values must be edited directly on those two nodes.

## Setup in 10 minutes

1. Import `/workflows/ai-speed-to-lead-engine.json` into n8n.
2. Create the 4 credentials above and attach them to the corresponding nodes (Google Sheets, Slack, SMTP, OpenAI — n8n will flag every node that needs one).
3. Duplicate this [Google Sheet template](#) (create a sheet named `Leads` with columns: `timestamp, name, email, phone, company, website, source, score, tier, emails_sent, responded, response_time_seconds, last_seen_at, last_email_sent_at, notes, row_number`) and paste its ID into `⚙️ CONFIG → google_sheet_id`.
4. Open `⚙️ CONFIG` and fill in: agency name, Calendly link, Slack channel, sender email, qualification criteria, score thresholds, AI model.
5. Update the channel/inbox on `Slack - Error Alert` and `Send Email - Error Alert` (see note above).
6. Activate the workflow and copy the **Production URL** from the `Webhook - New Lead` node into your website form / Typeform / Facebook Lead Ads integration.
7. Send one real test lead and confirm it shows up in the Sheet and you get the Slack/email notification.

## Estimated monthly cost (typical agency volume: ~200 leads/mo)

| Item | Cost |
|---|---|
| OpenAI (gpt-4o-mini, ~2 calls/lead avg for qualification + email) | ~$3–6/mo |
| Google Sheets, Slack, SMTP | $0 (free tiers cover this volume) |
| n8n (self-hosted or Starter cloud plan) | $0–24/mo depending on hosting |
| **Total** | **~$5–30/mo** |

Costs scale roughly linearly with lead volume; at 1,000 leads/mo expect ~$15–30/mo in OpenAI usage.

## Test results (2026-09-24)

Ran end-to-end via a local HTML test form and 3 realistic leads (hot/warm/cold-shaped). See `/screenshots/`:
- `lead1-hot-result.png`, `lead2-warm-result.png`, `lead3-cold-result.png` — all returned `HTTP 200 {"status":"received"}` in under 200ms (after the first cold-start call).
- Structural validation (`n8n_validate_workflow`): **0 errors**, 111 expressions checked.
- Field normalization verified against the actual webhook execution data (name/email/phone/company/website/message/source all mapped correctly).
- Tier-routing logic (hot/warm/cold Switch rules) verified in isolation against all 3 tiers — 100% correct routing.
- Error-handling path verified: Error Trigger fires, formats the message, and both Slack and Email alert nodes execute independently (one failing doesn't block the other).
- The AI qualification, CRM, Slack and email nodes could not be exercised against live external services during this test because no credentials exist yet on the build instance — they need the client's own API keys (see credentials table above) before the first live lead.
