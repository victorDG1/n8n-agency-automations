# AI Speed-to-Lead Engine — Sales Sheet

## 3-sentence pitch

Most agencies lose deals simply because nobody replies to a hot lead fast enough — studies show contacting a lead within 5 minutes makes you 21x more likely to qualify it, yet the average B2B response time is over 42 hours. The AI Speed-to-Lead Engine reads every inbound form/lead ad submission, scores and routes it with AI in seconds, and fires off a personalized reply and a Slack alert to your sales team before the prospect has closed the browser tab. It runs unattended 24/7, logs everything to a sheet for reporting, and never lets a lead go more than a few seconds without an instant "we got it" and, for hot leads, minutes without a real conversation starting.

## ROI

- **Time saved:** a human triaging and personally replying to ~200 leads/month at ~8 minutes each = ~27 hours/month of manual work eliminated.
- **Revenue impact:** industry data (Harvard Business Review / InsideSales.com) shows 5-minute response time vs. 30+ minutes can be the difference between qualifying a lead at all. Recovering even 2–3 extra closed deals/month from faster response, at a typical agency retainer of $2,000–5,000/mo, is $4,000–15,000/month in recovered/accelerated revenue for a workflow that costs under $30/month to run.
- **Payback:** the setup fee is typically recovered in the first qualified lead it saves from going cold.

## Suggested pricing

| | Price |
|---|---|
| Setup (install + brand + connect client's Sheet/Slack/SMTP/OpenAI + 1 test run) | **$750 – $1,500** one-time |
| Monthly retainer (monitoring, tweaks to qualification criteria/email tone, minor fixes) | **$150 – $300/mo** |
| AI/API costs (pass-through or bundled) | ~$5–30/mo depending on volume |

Position it as part of a broader "AI Ops" retainer if you already manage other automations for the client — the marginal cost of adding this workflow to an existing n8n instance is low.

## 90-second Loom script

1. **(0:00–0:15) Hook:** "Here's what happens the second someone fills out your contact form — before you even see the notification." Show the test form, submit a lead.
2. **(0:15–0:35) Instant response:** Show the `{"status":"received"}` response in under a second. "The form never makes them wait — but behind the scenes, AI is already reading this lead."
3. **(0:35–0:55) AI qualification + routing:** Switch to n8n, show the AI Qualification node's output (score, tier, summary) and the Switch node routing to the Hot branch. "It just scored this an 85 — hot lead — and it's about to alert your sales team and email the prospect a booking link, automatically."
4. **(0:55–1:15) Slack + email:** Show the Slack alert landing in the channel and the personalized email draft. "No copy-paste, no delay — this would normally take a rep 20 minutes to notice, write, and send."
5. **(1:15–1:30) Close:** Show the Google Sheet logging the lead with response time in seconds. "Every lead, every score, every response time — tracked automatically. This is the AI Speed-to-Lead Engine, and it can be live on your site this week."
