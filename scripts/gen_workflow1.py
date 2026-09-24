#!/usr/bin/env python3
"""Generates workflows/ai-speed-to-lead-engine.json for n8n import."""
import json

nodes = []
connections = {}

def full_type(t):
    if t.startswith("nodes-langchain."):
        return "@n8n/n8n-nodes-langchain." + t.split(".", 1)[1]
    if t.startswith("nodes-base."):
        return "n8n-nodes-base." + t.split(".", 1)[1]
    return t

def add_node(id_, name, type_, typeVersion, pos, params=None, creds=None, notes=None,
             retryOnFail=None, maxTries=None, waitBetweenTries=None, disabled=None):
    n = {
        "id": id_, "name": name, "type": full_type(type_), "typeVersion": typeVersion,
        "position": pos, "parameters": params or {},
    }
    if creds: n["credentials"] = creds
    if notes: n["notes"] = notes
    if retryOnFail is not None: n["retryOnFail"] = retryOnFail
    if maxTries is not None: n["maxTries"] = maxTries
    if waitBetweenTries is not None: n["waitBetweenTries"] = waitBetweenTries
    if disabled is not None: n["disabled"] = disabled
    nodes.append(n)
    return name

def connect(src, dst, src_type="main", src_index=0, dst_type="main", dst_index=0):
    connections.setdefault(src, {}).setdefault(src_type, [])
    lst = connections[src][src_type]
    while len(lst) <= src_index:
        lst.append([])
    lst[src_index].append({"node": dst, "type": dst_type, "index": dst_index})

STICKY = "nodes-base.stickyNote"

# ---------------------------------------------------------------------------
# 0. STICKY NOTES (overview + per-block)
# ---------------------------------------------------------------------------
add_node("sticky-overview", "Overview", STICKY, 1, [-360, -520],
    {"width": 620, "height": 460, "color": 4, "content":
"""## AI Speed-to-Lead Engine

Responds to and qualifies every inbound lead in under 60 seconds, 24/7.

**Flow:** Webhook -> Normalize -> Instant 200 response -> Dedup check (Google Sheets) -> Optional website enrichment -> AI qualification (scored 0-100, tier hot/warm/cold) -> Tier routing:
- HOT -> Slack alert + AI-personalized email with booking link, sent immediately
- WARM -> AI email + 2-step follow-up sequence (Wait 2d / Wait 3d), stops if the lead responds
- COLD -> short AI educational email + CRM tag

**Before you go live:**
1. Open the **⚙️ CONFIG** node and fill in your agency's details.
2. Create the 4 credentials listed in that node's note (Google Sheets, Slack, SMTP, OpenAI).
3. Duplicate the Google Sheet template (see /docs) and paste its ID into CONFIG.
4. Send a test POST to the Webhook node's Production URL.

See /docs/ai-speed-to-lead-engine.md for full setup (10 min)."""})

add_node("sticky-1-intake", "Sticky - Intake", STICKY, 1, [-360, 60],
    {"width": 1180, "height": 340, "color": 5, "content":
"""### 1️⃣ INTAKE & NORMALIZATION
Accepts POST from any source (website form, Typeform, Facebook Lead Ads via Graph API webhook). The Code node auto-detects the payload shape and maps it to a standard lead object: name, email, phone, company, website, message, source.

Responds to the webhook with `{"status":"received"}` (200) immediately after normalization — the form never waits for the AI or CRM calls, which continue in the background of the same execution."""})

add_node("sticky-2-dedup", "Sticky - Dedup", STICKY, 1, [860, 420],
    {"width": 900, "height": 320, "color": 3, "content":
"""### 2️⃣ DEDUPLICATION
Looks up the lead's email in the Google Sheets CRM tab. If found, updates the contact counter and stops (no duplicate emails/alerts).

**Alternative CRM:** the disabled \"HubSpot - Search Contact (Alt CRM)\" node below shows how to swap Google Sheets for HubSpot. Enable it, disable the Google Sheets dedup branch, and add a HubSpot credential."""})

add_node("sticky-3-enrich", "Sticky - Enrichment", STICKY, 1, [860, -420],
    {"width": 900, "height": 440, "color": 7, "content":
"""### 3️⃣ WEBSITE ENRICHMENT (optional, best-effort)
If the lead submitted a website, fetches the homepage and extracts the <title> and meta description to give the AI more context (industry, positioning). If the site is missing or the request fails, the workflow continues with empty enrichment fields — this never blocks qualification."""})

add_node("sticky-4-ai", "Sticky - AI Qualification", STICKY, 1, [1900, -420],
    {"width": 700, "height": 780, "color": 6, "content":
"""### 4️⃣ AI QUALIFICATION
The Basic LLM Chain scores the lead 0-100 and assigns a tier (hot/warm/cold) using the criteria you define in ⚙️ CONFIG. Output is forced into JSON via the Structured Output Parser (score, tier, intent, budget_signal, summary, recommended_next_step).

Retries 3x automatically on API errors/timeouts. If the parsed output still fails validation (e.g. score out of range), a safe fallback (tier=warm, score=50) is applied so the lead is never lost, and it's flagged in the sheet notes for manual review."""})

add_node("sticky-5-hot", "Sticky - Hot", STICKY, 1, [2900, -680],
    {"width": 640, "height": 320, "color": 4, "content":
"""### 5️⃣ HOT -> INSTANT RESPONSE
Slack alert to your sales channel with the AI summary + booking link, and a personalized email to the lead with the Calendly link — both fire within seconds of the qualification finishing."""})

add_node("sticky-6-warm", "Sticky - Warm", STICKY, 1, [2900, -60],
    {"width": 1980, "height": 500, "color": 5, "content":
"""### 6️⃣ WARM -> 3-EMAIL FOLLOW-UP SEQUENCE
Email 1 immediately, then Wait 2 days and check the sheet's `responded` column — if TRUE the sequence stops. Otherwise Email 2, Wait 3 days, check again, then Email 3 (final). Mark `responded=TRUE` in the sheet (manually or via your booking tool's webhook) any time to stop the sequence early."""})

add_node("sticky-7-cold", "Sticky - Cold", STICKY, 1, [2900, 500],
    {"width": 900, "height": 260, "color": 3, "content":
"""### 7️⃣ COLD -> EDUCATIONAL NURTURE
Short, low-pressure AI email (no hard sell) plus a `cold` tag in the sheet so sales knows not to prioritize this lead."""})

add_node("sticky-error", "Sticky - Error Handling", STICKY, 1, [-360, 820],
    {"width": 900, "height": 300, "color": 2, "content":
"""### ⚠️ ERROR HANDLING
Error Trigger fires whenever any node in this workflow fails after its retries are exhausted. Sends the workflow name, the failing node, and the error message to Slack and email so you catch problems (expired credentials, API outages) before a real lead is affected.

**Note:** this runs as its own isolated execution and cannot read ⚙️ CONFIG (that node never executed here) - the Slack channel and error email are hardcoded directly on the two nodes below. Update them there when reselling."""})

# ---------------------------------------------------------------------------
# 1. INTAKE
# ---------------------------------------------------------------------------
WEBHOOK = add_node("webhook", "Webhook - New Lead", "nodes-base.webhook", 2.1, [-360, 260],
    {"httpMethod": "POST", "path": "speed-to-lead-intake", "responseMode": "responseNode",
     "options": {}})

CONFIG = add_node("config", "⚙️ CONFIG", "nodes-base.set", 3.5, [-80, 260],
    {"mode": "manual", "includeOtherFields": True,
     "assignments": {"assignments": [
        {"id": "a1", "name": "agency_name", "type": "string", "value": "Your Agency Name"},
        {"id": "a2", "name": "calendly_link", "type": "string", "value": "https://calendly.com/your-agency/intro-call"},
        {"id": "a3", "name": "slack_channel", "type": "string", "value": "#hot-leads"},
        {"id": "a4", "name": "notification_email_from", "type": "string", "value": "leads@youragency.com"},
        {"id": "a5", "name": "google_sheet_id", "type": "string", "value": "PASTE_YOUR_GOOGLE_SHEET_ID_HERE"},
        {"id": "a6", "name": "google_sheet_tab", "type": "string", "value": "Leads"},
        {"id": "a7", "name": "hot_score_threshold", "type": "number", "value": 70},
        {"id": "a8", "name": "warm_score_threshold", "type": "number", "value": 40},
        {"id": "a9", "name": "qualification_criteria", "type": "string", "value":
            "HOT = clear budget signal, urgent timeline, or explicit request for a call/quote/proposal. "
            "WARM = genuine interest and a real business need, but missing budget or timeline details. "
            "COLD = vague inquiry, student/job seeker, spam-like content, or no real buying intent."},
        {"id": "a10", "name": "email_tone", "type": "string", "value": "friendly, professional, concise, no corporate jargon, written as if from a helpful human on the team"},
        {"id": "a11", "name": "follow_up_wait_1_days", "type": "number", "value": 2},
        {"id": "a12", "name": "follow_up_wait_2_days", "type": "number", "value": 3},
        {"id": "a13", "name": "ai_model", "type": "string", "value": "gpt-4o-mini"},
     ]},
     "options": {}},
    notes=("Every client-specific setting lives here. To resell this workflow, duplicate it and edit ONLY this node.\n\n"
           "Credentials to create on the client's n8n instance:\n"
           "1. Google Sheets OAuth2 (CRM log + dedup)\n"
           "2. Slack API / Bot Token (channel alerts)\n"
           "3. SMTP (outbound email)\n"
           "4. OpenAI API (lead qualification + email writing)"))

NORMALIZE_CODE = r'''// Detect the webhook payload shape (generic web form, Typeform, or Facebook Lead Ads)
// and map it to one standard lead object. A Code node is used here because the three
// source formats are structurally different (flat body vs. Typeform answers[] vs.
// Facebook field_data[]) and cannot be reduced to a single Set-node expression.
const item = $input.first().json;
const body = item.body || {};
const cfg = item; // CONFIG fields were merged onto this item upstream

let lead = { name: '', email: '', phone: '', company: '', website: '', message: '', source: 'website_form' };

if (body.form_response) {
  // Typeform webhook
  lead.source = 'typeform';
  const answers = body.form_response.answers || [];
  for (const a of answers) {
    const ref = ((a.field && a.field.ref) || '').toLowerCase();
    if (a.type === 'email') lead.email = a.email;
    else if (a.type === 'phone_number') lead.phone = a.phone_number;
    else if (a.type === 'website') lead.website = a.website;
    else if (ref.includes('company')) lead.company = a.text || '';
    else if (ref.includes('name')) lead.name = a.text || '';
    else if (a.type === 'text' || a.type === 'long_text') lead.message = lead.message ? `${lead.message} ${a.text}` : (a.text || '');
  }
} else if (body.entry) {
  // Facebook Lead Ads (Graph API leadgen change notification)
  lead.source = 'facebook_lead_ads';
  const value = body.entry?.[0]?.changes?.[0]?.value || {};
  const fields = value.field_data || body.field_data || [];
  for (const f of fields) {
    const key = (f.name || '').toLowerCase();
    const val = (f.values && f.values[0]) || '';
    if (key.includes('email')) lead.email = val;
    else if (key.includes('phone')) lead.phone = val;
    else if (key.includes('company')) lead.company = val;
    else if (key.includes('website')) lead.website = val;
    else if (key.includes('name')) lead.name = val;
    else if (key.includes('message') || key.includes('note')) lead.message = val;
  }
} else {
  // Generic website form / HTML POST - accepts common field name variants
  lead.source = body.source || 'website_form';
  lead.name = body.name || body.full_name || body.fullName || '';
  lead.email = body.email || body.Email || '';
  lead.phone = body.phone || body.phone_number || body.tel || '';
  lead.company = body.company || body.company_name || '';
  lead.website = body.website || body.url || '';
  lead.message = body.message || body.notes || body.details || '';
}

return [{
  json: {
    ...cfg,
    name: (lead.name || '').trim(),
    email: (lead.email || '').trim().toLowerCase(),
    phone: (lead.phone || '').trim(),
    company: (lead.company || '').trim(),
    website: (lead.website || '').trim(),
    message: (lead.message || '').trim(),
    source: lead.source,
    received_at: new Date().toISOString(),
  },
}];
'''

NORMALIZE = add_node("normalize", "Normalize Lead Fields", "nodes-base.code", 2, [180, 260],
    {"mode": "runOnceForAllItems", "language": "javaScript", "jsCode": NORMALIZE_CODE})

RESPOND = add_node("respond", "Respond to Webhook", "nodes-base.respondToWebhook", 1.5, [440, 60],
    {"respondWith": "json", "responseBody": '{\n  "status": "received"\n}',
     "options": {"responseCode": 200}})

connect(WEBHOOK, CONFIG)
connect(CONFIG, NORMALIZE)
connect(NORMALIZE, RESPOND)

# ---------------------------------------------------------------------------
# 2. DEDUPLICATION
# ---------------------------------------------------------------------------
DEDUP = add_node("dedup-search", "Dedup - Search Existing Lead", "nodes-base.googleSheets", 4.7, [440, 420],
    {"resource": "sheet", "operation": "read",
     "documentId": {"mode": "id", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_id }}"},
     "sheetName": {"mode": "name", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_tab }}"},
     "filtersUI": {"values": [{"lookupColumn": "email", "lookupValue": "={{ $json.email }}"}]},
     "options": {"returnFirstMatch": True}},
    creds={"googleSheetsOAuth2Api": {"id": "PLACEHOLDER", "name": "Google Sheets account"}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)

HUBSPOT_ALT = add_node("hubspot-alt", "HubSpot - Search Contact (Alt CRM)", "nodes-base.hubspot", 2, [440, 560],
    {"resource": "contact", "operation": "getAll", "returnAll": False, "limit": 1,
     "filters": {}, "additionalFields": {}},
    creds={"hubspotApi": {"id": "PLACEHOLDER", "name": "HubSpot account"}}, disabled=True,
    notes="Disabled by default. Enable this instead of the Google Sheets dedup branch if the client's CRM is HubSpot.")

IF_EXISTS = add_node("if-exists", "IF - Email Already Exists?", "nodes-base.if", 2.3, [700, 420],
    {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
        "conditions": [{"id": "c1", "leftValue": "={{ $json.rowNumber }}", "rightValue": "",
                         "operator": {"type": "number", "operation": "exists"}}], "combinator": "and"}})

MARK_DUP = add_node("mark-dup", "Mark Duplicate - Update Sheet", "nodes-base.googleSheets", 4.7, [960, 560],
    {"resource": "sheet", "operation": "update",
     "documentId": {"mode": "id", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_id }}"},
     "sheetName": {"mode": "name", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_tab }}"},
     "columns": {"mappingMode": "defineBelow", "value": {
        "row_number": "={{ $json.rowNumber }}",
        "last_seen_at": "={{ $now.toISO() }}",
     }, "matchingColumns": ["row_number"]},
     "options": {}},
    creds={"googleSheetsOAuth2Api": {"id": "PLACEHOLDER", "name": "Google Sheets account"}})

DUP_STOP = add_node("dup-stop", "No Operation - Duplicate Skipped", "nodes-base.noOp", 1, [1220, 560], {})

connect(NORMALIZE, DEDUP)
connect(NORMALIZE, HUBSPOT_ALT)
connect(HUBSPOT_ALT, IF_EXISTS)
connect(DEDUP, IF_EXISTS)
connect(IF_EXISTS, MARK_DUP, src_index=0)
connect(MARK_DUP, DUP_STOP)

# ---------------------------------------------------------------------------
# 3. ENRICHMENT
# ---------------------------------------------------------------------------
IF_WEBSITE = add_node("if-website", "IF - Has Website?", "nodes-base.if", 2.3, [960, 220],
    {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
        "conditions": [{"id": "c1", "leftValue": "={{ $json.website }}", "rightValue": "",
                         "operator": {"type": "string", "operation": "notEmpty"}}], "combinator": "and"}})

FETCH_SITE = add_node("fetch-site", "HTTP Request - Fetch Homepage", "nodes-base.httpRequest", 4.5, [1220, 80],
    {"method": "GET", "url": "={{ $json.website }}", "authentication": "none",
     "options": {"timeout": 8000, "redirect": {"redirect": {"followRedirects": True}}}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000, notes="Best-effort. If the site is down or blocks bots, downstream nodes fall back to empty enrichment.")

EXTRACT_HTML = add_node("extract-html", "HTML Extract - Title & Description", "nodes-base.htmlExtract", 1, [1480, 80],
    {"sourceData": "json", "dataPropertyName": "data",
     "extractionValues": {"values": [
        {"key": "page_title", "cssSelector": "title", "returnValue": "text"},
        {"key": "page_description", "cssSelector": "meta[name=\"description\"]", "returnValue": "attribute", "returnAttribute": "content"},
     ]}, "options": {}})

ENRICH_YES = add_node("enrich-yes", "Set - Enrichment From Website", "nodes-base.set", 3.5, [1740, 80],
    {"mode": "manual", "includeOtherFields": True,
     "assignments": {"assignments": [
        {"id": "e1", "name": "page_title", "type": "string", "value": "={{ $json.page_title || '' }}"},
        {"id": "e2", "name": "page_description", "type": "string", "value": "={{ $json.page_description || '' }}"},
     ]}, "options": {}})

ENRICH_NO = add_node("enrich-no", "Set - No Enrichment", "nodes-base.set", 3.5, [1220, 320],
    {"mode": "manual", "includeOtherFields": True,
     "assignments": {"assignments": [
        {"id": "e1", "name": "page_title", "type": "string", "value": ""},
        {"id": "e2", "name": "page_description", "type": "string", "value": ""},
     ]}, "options": {}})

connect(IF_EXISTS, IF_WEBSITE, src_index=1)
connect(IF_WEBSITE, FETCH_SITE, src_index=0)
connect(FETCH_SITE, EXTRACT_HTML)
connect(EXTRACT_HTML, ENRICH_YES)
connect(IF_WEBSITE, ENRICH_NO, src_index=1)

# ---------------------------------------------------------------------------
# 4. AI QUALIFICATION
# ---------------------------------------------------------------------------
QUALIFY_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "score": {"type": "number", "description": "0-100 lead quality score"},
        "tier": {"type": "string", "enum": ["hot", "warm", "cold"]},
        "intent": {"type": "string"},
        "budget_signal": {"type": "string"},
        "summary": {"type": "string"},
        "recommended_next_step": {"type": "string"},
    },
    "required": ["score", "tier", "intent", "budget_signal", "summary", "recommended_next_step"],
}, indent=2)

CHAT_MODEL = add_node("chat-model", "OpenAI Chat Model - Shared", "nodes-langchain.lmChatOpenAi", 1.3, [2000, 340],
    {"model": {"mode": "id", "value": "={{ $('⚙️ CONFIG').item.json.ai_model }}"},
     "options": {"temperature": 0.3}},
    creds={"openAiApi": {"id": "PLACEHOLDER", "name": "OpenAI account"}})

QUALIFY_PARSER = add_node("qualify-parser", "Structured Output Parser - Qualification", "nodes-langchain.outputParserStructured", 1.3, [2260, 340],
    {"schemaType": "manual", "inputSchema": QUALIFY_SCHEMA})

QUALIFY_PROMPT = (
    "You are a B2B lead qualification assistant for a marketing agency called {{ $('⚙️ CONFIG').item.json.agency_name }}.\n\n"
    "Qualification criteria:\n{{ $('⚙️ CONFIG').item.json.qualification_criteria }}\n\n"
    "Lead data:\n"
    "- Name: {{ $json.name }}\n"
    "- Company: {{ $json.company }}\n"
    "- Email: {{ $json.email }}\n"
    "- Phone: {{ $json.phone }}\n"
    "- Website: {{ $json.website }}\n"
    "- Message: {{ $json.message }}\n"
    "- Website title: {{ $json.page_title }}\n"
    "- Website description: {{ $json.page_description }}\n\n"
    "Return ONLY a JSON object (json) scoring this lead 0-100 and classifying it into tier hot, warm or cold, "
    "using the exact thresholds: hot >= {{ $('⚙️ CONFIG').item.json.hot_score_threshold }}, "
    "warm >= {{ $('⚙️ CONFIG').item.json.warm_score_threshold }}, otherwise cold."
)

QUALIFY_CHAIN = add_node("qualify-chain", "Basic LLM Chain - Qualify Lead", "nodes-langchain.chainLlm", 1.9, [2000, 220],
    {"promptType": "define", "text": QUALIFY_PROMPT, "hasOutputParser": True, "options": {}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)

connect(ENRICH_YES, QUALIFY_CHAIN)
connect(ENRICH_NO, QUALIFY_CHAIN)
connect(CHAT_MODEL, QUALIFY_CHAIN, src_type="ai_languageModel", dst_type="ai_languageModel")
connect(QUALIFY_PARSER, QUALIFY_CHAIN, src_type="ai_outputParser", dst_type="ai_outputParser")

IF_VALID = add_node("if-valid", "IF - Valid AI Output?", "nodes-base.if", 2.3, [2260, 220],
    {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
        "conditions": [
            {"id": "v1", "leftValue": "={{ $json.output.tier }}", "rightValue": "hot,warm,cold",
             "operator": {"type": "string", "operation": "regex"}},
        ], "combinator": "and"}})

FALLBACK = add_node("fallback", "Set - Fallback Qualification", "nodes-base.set", 3.5, [2260, 400],
    {"mode": "manual", "includeOtherFields": True,
     "assignments": {"assignments": [
        {"id": "f1", "name": "output.tier", "type": "string", "value": "warm"},
        {"id": "f2", "name": "output.score", "type": "number", "value": 50},
        {"id": "f3", "name": "output.summary", "type": "string", "value": "AI qualification output failed validation - routed to WARM as a safe default. Review manually."},
        {"id": "f4", "name": "output.recommended_next_step", "type": "string", "value": "Manual review recommended."},
     ]}, "options": {}})

connect(QUALIFY_CHAIN, IF_VALID)
connect(IF_VALID, FALLBACK, src_index=1)

# ---------------------------------------------------------------------------
# 5. SWITCH BY TIER
# ---------------------------------------------------------------------------
SWITCH = add_node("switch-tier", "Switch - Route by Tier", "nodes-base.switch", 3.4, [2520, 220],
    {"mode": "rules", "rules": {"values": [
        {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
            "conditions": [{"id": "s1", "leftValue": "={{ $json.output.tier }}", "rightValue": "hot",
                             "operator": {"type": "string", "operation": "equals"}}], "combinator": "and"},
         "outputKey": "hot"},
        {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
            "conditions": [{"id": "s2", "leftValue": "={{ $json.output.tier }}", "rightValue": "warm",
                             "operator": {"type": "string", "operation": "equals"}}], "combinator": "and"},
         "outputKey": "warm"},
        {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
            "conditions": [{"id": "s3", "leftValue": "={{ $json.output.tier }}", "rightValue": "cold",
                             "operator": {"type": "string", "operation": "equals"}}], "combinator": "and"},
         "outputKey": "cold"},
     ]},
     "options": {"fallbackOutput": "1"}})  # unmatched tiers fall through to WARM (index 1)

connect(IF_VALID, SWITCH, src_index=0)
connect(FALLBACK, SWITCH)

EMAIL_SCHEMA = json.dumps({
    "type": "object",
    "properties": {"subject": {"type": "string"}, "body": {"type": "string"}},
    "required": ["subject", "body"],
}, indent=2)

EMAIL_PARSER = add_node("email-parser", "Structured Output Parser - Email", "nodes-langchain.outputParserStructured", 1.3, [2780, 620],
    {"schemaType": "manual", "inputSchema": EMAIL_SCHEMA})

# ---------------------------------------------------------------------------
# 6. HOT BRANCH
# ---------------------------------------------------------------------------
HOT_PROMPT = (
    "Write a short, personal follow-up email (json) to a HOT lead for {{ $('⚙️ CONFIG').item.json.agency_name }}.\n"
    "Tone: {{ $('⚙️ CONFIG').item.json.email_tone }}.\n"
    "Lead name: {{ $json.name }}. Company: {{ $json.company }}. Their message: {{ $json.message }}.\n"
    "AI summary: {{ $json.output.summary }}. Recommended next step: {{ $json.output.recommended_next_step }}.\n"
    "Include this scheduling link once, naturally: {{ $('⚙️ CONFIG').item.json.calendly_link }}.\n"
    "Return an object with subject and body (plain text, no markdown, sign off as the {{ $('⚙️ CONFIG').item.json.agency_name }} team)."
)
HOT_CHAIN = add_node("hot-chain", "Basic LLM Chain - Write Hot Email", "nodes-langchain.chainLlm", 1.9, [2780, -680],
    {"promptType": "define", "text": HOT_PROMPT, "hasOutputParser": True, "options": {}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)

HOT_EMAIL = add_node("hot-email", "Send Email - Hot Lead", "nodes-base.emailSend", 2.1, [3040, -680],
    {"fromEmail": "={{ $('⚙️ CONFIG').item.json.notification_email_from }}",
     "toEmail": "={{ $json.email }}",
     "subject": "={{ $json.output.subject }}",
     "text": "={{ $json.output.body }}", "options": {}},
    creds={"smtp": {"id": "PLACEHOLDER", "name": "SMTP account"}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)

HOT_SLACK = add_node("hot-slack", "Slack - Alert Hot Lead", "nodes-base.slack", 2.7, [2780, -540],
    {"resource": "message", "operation": "post",
     "select": "channel",
     "channelId": {"mode": "id", "value": "={{ $('⚙️ CONFIG').item.json.slack_channel }}"},
     "text": "=🔥 *HOT LEAD* — {{ $json.name }} ({{ $json.company }})\\nScore: {{ $json.output.score }}/100\\nIntent: {{ $json.output.intent }}\\nBudget signal: {{ $json.output.budget_signal }}\\nSummary: {{ $json.output.summary }}\\nEmail: {{ $json.email }} | Phone: {{ $json.phone }}\\n<{{ $('⚙️ CONFIG').item.json.calendly_link }}|Book a call now>",
     "otherOptions": {}},
    creds={"slackApi": {"id": "PLACEHOLDER", "name": "Slack account"}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)

HOT_LOG = add_node("hot-log", "Google Sheets - Log Hot Lead", "nodes-base.googleSheets", 4.7, [3300, -610],
    {"resource": "sheet", "operation": "appendOrUpdate",
     "documentId": {"mode": "id", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_id }}"},
     "sheetName": {"mode": "name", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_tab }}"},
     "columns": {"mappingMode": "defineBelow", "value": {
        "email": "={{ $json.email }}", "name": "={{ $json.name }}", "company": "={{ $json.company }}",
        "phone": "={{ $json.phone }}", "source": "={{ $json.source }}",
        "timestamp": "={{ $json.received_at }}", "score": "={{ $json.output.score }}",
        "tier": "={{ $json.output.tier }}", "emails_sent": 1, "responded": False,
        "response_time_seconds": "={{ Math.round((Date.now() - Date.parse($json.received_at)) / 1000) }}",
        "notes": "={{ $json.output.summary }}",
     }, "matchingColumns": ["email"]},
     "options": {}},
    creds={"googleSheetsOAuth2Api": {"id": "PLACEHOLDER", "name": "Google Sheets account"}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)

connect(SWITCH, HOT_CHAIN, src_index=0)
connect(SWITCH, HOT_SLACK, src_index=0)
connect(CHAT_MODEL, HOT_CHAIN, src_type="ai_languageModel", dst_type="ai_languageModel")
connect(EMAIL_PARSER, HOT_CHAIN, src_type="ai_outputParser", dst_type="ai_outputParser")
connect(HOT_CHAIN, HOT_EMAIL)
connect(HOT_EMAIL, HOT_LOG)
connect(HOT_SLACK, HOT_LOG)

# ---------------------------------------------------------------------------
# 7. WARM BRANCH (3-step sequence)
# ---------------------------------------------------------------------------
def warm_email_prompt(n):
    ordinal = {1: "first", 2: "second (a gentle nudge)", 3: "third and final (last check-in, low pressure)"}[n]
    return (
        f"Write the {ordinal} follow-up email (json) to a WARM lead for {{{{ $('⚙️ CONFIG').item.json.agency_name }}}}.\n"
        "Tone: {{ $('⚙️ CONFIG').item.json.email_tone }}.\n"
        "Lead name: {{ $json.name }}. Company: {{ $json.company }}. Their message: {{ $json.message }}.\n"
        "AI summary: {{ $json.output.summary }}.\n"
        "Return an object with subject and body (plain text, no markdown, sign off as the {{ $('⚙️ CONFIG').item.json.agency_name }} team)."
    )

WARM1_CHAIN = add_node("warm1-chain", "Basic LLM Chain - Write Warm Email 1", "nodes-langchain.chainLlm", 1.9, [2780, -60],
    {"promptType": "define", "text": warm_email_prompt(1), "hasOutputParser": True, "options": {}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)
WARM1_EMAIL = add_node("warm1-email", "Send Email - Warm 1", "nodes-base.emailSend", 2.1, [3040, -60],
    {"fromEmail": "={{ $('⚙️ CONFIG').item.json.notification_email_from }}", "toEmail": "={{ $json.email }}",
     "subject": "={{ $json.output.subject }}", "text": "={{ $json.output.body }}", "options": {}},
    creds={"smtp": {"id": "PLACEHOLDER", "name": "SMTP account"}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)
WARM1_LOG = add_node("warm1-log", "Google Sheets - Log Warm 1", "nodes-base.googleSheets", 4.7, [3300, -60],
    {"resource": "sheet", "operation": "appendOrUpdate",
     "documentId": {"mode": "id", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_id }}"},
     "sheetName": {"mode": "name", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_tab }}"},
     "columns": {"mappingMode": "defineBelow", "value": {
        "email": "={{ $json.email }}", "name": "={{ $json.name }}", "company": "={{ $json.company }}",
        "phone": "={{ $json.phone }}", "source": "={{ $json.source }}",
        "timestamp": "={{ $json.received_at }}", "score": "={{ $json.output.score }}",
        "tier": "warm", "emails_sent": 1, "responded": False,
        "response_time_seconds": "={{ Math.round((Date.now() - Date.parse($json.received_at)) / 1000) }}",
        "notes": "={{ $json.output.summary }}",
     }, "matchingColumns": ["email"]},
     "options": {}},
    creds={"googleSheetsOAuth2Api": {"id": "PLACEHOLDER", "name": "Google Sheets account"}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)
WAIT1 = add_node("wait1", "Wait - 2 Days", "nodes-base.wait", 1.1, [3560, -60],
    {"resume": "timeInterval", "amount": "={{ $('⚙️ CONFIG').item.json.follow_up_wait_1_days }}", "unit": "days"})
CHECK1 = add_node("check1", "Google Sheets - Check Responded 1", "nodes-base.googleSheets", 4.7, [3820, -60],
    {"resource": "sheet", "operation": "read",
     "documentId": {"mode": "id", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_id }}"},
     "sheetName": {"mode": "name", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_tab }}"},
     "filtersUI": {"values": [{"lookupColumn": "email", "lookupValue": "={{ $('Normalize Lead Fields').item.json.email }}"}]},
     "options": {"returnFirstMatch": True}},
    creds={"googleSheetsOAuth2Api": {"id": "PLACEHOLDER", "name": "Google Sheets account"}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)
IF_RESP1 = add_node("if-resp1", "IF - Responded After Email 1?", "nodes-base.if", 2.3, [4080, -60],
    {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"},
        "conditions": [{"id": "r1", "leftValue": "={{ $json.responded }}", "rightValue": True,
                         "operator": {"type": "boolean", "operation": "equals"}}], "combinator": "and"}})
STOP1 = add_node("stop1", "No Operation - Sequence Stopped 1", "nodes-base.noOp", 1, [4340, -220], {})

WARM2_CHAIN = add_node("warm2-chain", "Basic LLM Chain - Write Warm Email 2", "nodes-langchain.chainLlm", 1.9, [4340, 80],
    {"promptType": "define", "text": warm_email_prompt(2), "hasOutputParser": True, "options": {}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)
WARM2_EMAIL = add_node("warm2-email", "Send Email - Warm 2", "nodes-base.emailSend", 2.1, [4600, 80],
    {"fromEmail": "={{ $('⚙️ CONFIG').item.json.notification_email_from }}", "toEmail": "={{ $('Normalize Lead Fields').item.json.email }}",
     "subject": "={{ $json.output.subject }}", "text": "={{ $json.output.body }}", "options": {}},
    creds={"smtp": {"id": "PLACEHOLDER", "name": "SMTP account"}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)
WARM2_LOG = add_node("warm2-log", "Google Sheets - Log Warm 2", "nodes-base.googleSheets", 4.7, [4860, 80],
    {"resource": "sheet", "operation": "appendOrUpdate",
     "documentId": {"mode": "id", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_id }}"},
     "sheetName": {"mode": "name", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_tab }}"},
     "columns": {"mappingMode": "defineBelow", "value": {
        "email": "={{ $('Normalize Lead Fields').item.json.email }}", "emails_sent": 2,
        "last_email_sent_at": "={{ $now.toISO() }}",
     }, "matchingColumns": ["email"]}, "options": {}},
    creds={"googleSheetsOAuth2Api": {"id": "PLACEHOLDER", "name": "Google Sheets account"}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)
WAIT2 = add_node("wait2", "Wait - 3 Days", "nodes-base.wait", 1.1, [5120, 80],
    {"resume": "timeInterval", "amount": "={{ $('⚙️ CONFIG').item.json.follow_up_wait_2_days }}", "unit": "days"})
CHECK2 = add_node("check2", "Google Sheets - Check Responded 2", "nodes-base.googleSheets", 4.7, [5380, 80],
    {"resource": "sheet", "operation": "read",
     "documentId": {"mode": "id", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_id }}"},
     "sheetName": {"mode": "name", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_tab }}"},
     "filtersUI": {"values": [{"lookupColumn": "email", "lookupValue": "={{ $('Normalize Lead Fields').item.json.email }}"}]},
     "options": {"returnFirstMatch": True}},
    creds={"googleSheetsOAuth2Api": {"id": "PLACEHOLDER", "name": "Google Sheets account"}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)
IF_RESP2 = add_node("if-resp2", "IF - Responded After Email 2?", "nodes-base.if", 2.3, [5640, 80],
    {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"},
        "conditions": [{"id": "r2", "leftValue": "={{ $json.responded }}", "rightValue": True,
                         "operator": {"type": "boolean", "operation": "equals"}}], "combinator": "and"}})
STOP2 = add_node("stop2", "No Operation - Sequence Stopped 2", "nodes-base.noOp", 1, [5900, -80], {})

WARM3_CHAIN = add_node("warm3-chain", "Basic LLM Chain - Write Warm Email 3", "nodes-langchain.chainLlm", 1.9, [5900, 240],
    {"promptType": "define", "text": warm_email_prompt(3), "hasOutputParser": True, "options": {}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)
WARM3_EMAIL = add_node("warm3-email", "Send Email - Warm 3", "nodes-base.emailSend", 2.1, [6160, 240],
    {"fromEmail": "={{ $('⚙️ CONFIG').item.json.notification_email_from }}", "toEmail": "={{ $('Normalize Lead Fields').item.json.email }}",
     "subject": "={{ $json.output.subject }}", "text": "={{ $json.output.body }}", "options": {}},
    creds={"smtp": {"id": "PLACEHOLDER", "name": "SMTP account"}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)
WARM3_LOG = add_node("warm3-log", "Google Sheets - Log Warm 3 Final", "nodes-base.googleSheets", 4.7, [6420, 240],
    {"resource": "sheet", "operation": "appendOrUpdate",
     "documentId": {"mode": "id", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_id }}"},
     "sheetName": {"mode": "name", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_tab }}"},
     "columns": {"mappingMode": "defineBelow", "value": {
        "email": "={{ $('Normalize Lead Fields').item.json.email }}", "emails_sent": 3,
        "last_email_sent_at": "={{ $now.toISO() }}", "notes": "Warm sequence complete (3/3 emails sent)",
     }, "matchingColumns": ["email"]}, "options": {}},
    creds={"googleSheetsOAuth2Api": {"id": "PLACEHOLDER", "name": "Google Sheets account"}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)

connect(SWITCH, WARM1_CHAIN, src_index=1)
connect(CHAT_MODEL, WARM1_CHAIN, src_type="ai_languageModel", dst_type="ai_languageModel")
connect(EMAIL_PARSER, WARM1_CHAIN, src_type="ai_outputParser", dst_type="ai_outputParser")
connect(WARM1_CHAIN, WARM1_EMAIL)
connect(WARM1_EMAIL, WARM1_LOG)
connect(WARM1_LOG, WAIT1)
connect(WAIT1, CHECK1)
connect(CHECK1, IF_RESP1)
connect(IF_RESP1, STOP1, src_index=0)
connect(IF_RESP1, WARM2_CHAIN, src_index=1)
connect(CHAT_MODEL, WARM2_CHAIN, src_type="ai_languageModel", dst_type="ai_languageModel")
connect(EMAIL_PARSER, WARM2_CHAIN, src_type="ai_outputParser", dst_type="ai_outputParser")
connect(WARM2_CHAIN, WARM2_EMAIL)
connect(WARM2_EMAIL, WARM2_LOG)
connect(WARM2_LOG, WAIT2)
connect(WAIT2, CHECK2)
connect(CHECK2, IF_RESP2)
connect(IF_RESP2, STOP2, src_index=0)
connect(IF_RESP2, WARM3_CHAIN, src_index=1)
connect(CHAT_MODEL, WARM3_CHAIN, src_type="ai_languageModel", dst_type="ai_languageModel")
connect(EMAIL_PARSER, WARM3_CHAIN, src_type="ai_outputParser", dst_type="ai_outputParser")
connect(WARM3_CHAIN, WARM3_EMAIL)
connect(WARM3_EMAIL, WARM3_LOG)

# ---------------------------------------------------------------------------
# 8. COLD BRANCH
# ---------------------------------------------------------------------------
COLD_PROMPT = (
    "Write a short educational email (json) to a COLD lead for {{ $('⚙️ CONFIG').item.json.agency_name }} - "
    "no hard sell, just one useful tip related to their message, and a soft invitation to reach out later.\n"
    "Tone: {{ $('⚙️ CONFIG').item.json.email_tone }}.\n"
    "Lead name: {{ $json.name }}. Their message: {{ $json.message }}.\n"
    "Return an object with subject and body (plain text, no markdown, sign off as the {{ $('⚙️ CONFIG').item.json.agency_name }} team)."
)
COLD_CHAIN = add_node("cold-chain", "Basic LLM Chain - Write Cold Email", "nodes-langchain.chainLlm", 1.9, [2780, 500],
    {"promptType": "define", "text": COLD_PROMPT, "hasOutputParser": True, "options": {}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)
COLD_EMAIL = add_node("cold-email", "Send Email - Cold", "nodes-base.emailSend", 2.1, [3040, 500],
    {"fromEmail": "={{ $('⚙️ CONFIG').item.json.notification_email_from }}", "toEmail": "={{ $json.email }}",
     "subject": "={{ $json.output.subject }}", "text": "={{ $json.output.body }}", "options": {}},
    creds={"smtp": {"id": "PLACEHOLDER", "name": "SMTP account"}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)
COLD_LOG = add_node("cold-log", "Google Sheets - Log Cold Lead", "nodes-base.googleSheets", 4.7, [3300, 500],
    {"resource": "sheet", "operation": "appendOrUpdate",
     "documentId": {"mode": "id", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_id }}"},
     "sheetName": {"mode": "name", "value": "={{ $('⚙️ CONFIG').item.json.google_sheet_tab }}"},
     "columns": {"mappingMode": "defineBelow", "value": {
        "email": "={{ $json.email }}", "name": "={{ $json.name }}", "company": "={{ $json.company }}",
        "phone": "={{ $json.phone }}", "source": "={{ $json.source }}",
        "timestamp": "={{ $json.received_at }}", "score": "={{ $json.output.score }}",
        "tier": "cold", "emails_sent": 1, "responded": False,
        "response_time_seconds": "={{ Math.round((Date.now() - Date.parse($json.received_at)) / 1000) }}",
        "notes": "={{ $json.output.summary }}",
     }, "matchingColumns": ["email"]}, "options": {}},
    creds={"googleSheetsOAuth2Api": {"id": "PLACEHOLDER", "name": "Google Sheets account"}},
    retryOnFail=True, maxTries=3, waitBetweenTries=2000)

connect(SWITCH, COLD_CHAIN, src_index=2)
connect(CHAT_MODEL, COLD_CHAIN, src_type="ai_languageModel", dst_type="ai_languageModel")
connect(EMAIL_PARSER, COLD_CHAIN, src_type="ai_outputParser", dst_type="ai_outputParser")
connect(COLD_CHAIN, COLD_EMAIL)
connect(COLD_EMAIL, COLD_LOG)

# ---------------------------------------------------------------------------
# 9. ERROR HANDLING
# ---------------------------------------------------------------------------
ERR_TRIGGER = add_node("err-trigger", "Error Trigger", "nodes-base.errorTrigger", 1, [-360, 900], {})
ERR_FORMAT = add_node("err-format", "Set - Format Error Message", "nodes-base.set", 3.5, [-80, 900],
    {"mode": "manual", "assignments": {"assignments": [
        {"id": "er1", "name": "workflow_name", "type": "string", "value": "={{ $json.workflow.name }}"},
        {"id": "er2", "name": "failed_node", "type": "string", "value": "={{ $json.execution.lastNodeExecuted }}"},
        {"id": "er3", "name": "error_message", "type": "string", "value": "={{ $json.execution.error.message }}"},
        {"id": "er4", "name": "execution_url", "type": "string", "value": "={{ $json.execution.url }}"},
     ]}, "options": {}})
ERR_SLACK = add_node("err-slack", "Slack - Error Alert", "nodes-base.slack", 2.7, [180, 820],
    {"resource": "message", "operation": "post", "select": "channel",
     "channelId": {"mode": "id", "value": "={{ '#hot-leads' }}"},
     "text": "=🚨 *Workflow error* in *{{ $json.workflow_name }}*\\nNode: {{ $json.failed_node }}\\nError: {{ $json.error_message }}\\n{{ $json.execution_url }}",
     "otherOptions": {}},
    creds={"slackApi": {"id": "PLACEHOLDER", "name": "Slack account"}},
    notes=("The Error Trigger runs in its own isolated execution, so it CANNOT read the ⚙️ CONFIG node "
           "(that node never ran in this execution). The Slack channel here is hardcoded on purpose - "
           "update it directly (and the From/To Email on 'Send Email - Error Alert') to match your ops "
           "channel/inbox when reselling this workflow."))
ERR_SLACK_NODE = nodes[-1]
ERR_SLACK_NODE["onError"] = "continueRegularOutput"
ERR_EMAIL = add_node("err-email", "Send Email - Error Alert", "nodes-base.emailSend", 2.1, [180, 980],
    {"fromEmail": "alerts@youragency.com", "toEmail": "you@youragency.com",
     "subject": "=Workflow error: {{ $json.workflow_name }}",
     "text": "=Node: {{ $json.failed_node }}\\nError: {{ $json.error_message }}\\nExecution: {{ $json.execution_url }}",
     "options": {}},
    creds={"smtp": {"id": "PLACEHOLDER", "name": "SMTP account"}})
nodes[-1]["onError"] = "continueRegularOutput"

connect(ERR_TRIGGER, ERR_FORMAT)
connect(ERR_FORMAT, ERR_SLACK)
connect(ERR_FORMAT, ERR_EMAIL)

# ---------------------------------------------------------------------------
workflow = {
    "name": "AI Speed-to-Lead Engine",
    "nodes": nodes,
    "connections": connections,
    "settings": {"executionOrder": "v1"},
}

with open("/home/agen/n8n-agency-automations/workflows/ai-speed-to-lead-engine.json", "w") as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"Generated {len(nodes)} nodes.")
